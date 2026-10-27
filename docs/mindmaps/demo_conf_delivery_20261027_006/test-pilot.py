import copy,json,tempfile,unittest,sqlite3,hashlib
from pathlib import Path
import workflow
from secure_app import create_app
from pilot import preview_import,reconcile
ROOT=Path(__file__).parent
PASSWORD='Fictief-test-wachtwoord-2026'
class PilotTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.state=Path(self.tmp.name)/'state';self.state.mkdir();(self.state/'workflow.json').write_bytes((ROOT/'live-reference.json').read_bytes());self.app=create_app(self.state);self.app.testing=True
  self.clients={}
  for name,role,employee in [('owner','owner',''),('bram','mechanic','Bram'),('admin','administration','')]:
   self.app.accounts.create(dict(username=name,password=PASSWORD,role=role,employee=employee));c=self.app.test_client();r=c.post('/api/login',json=dict(username=name,password=PASSWORD));self.assertEqual(r.status_code,200);self.clients[name]=(c,r.json['csrf'])
 def tearDown(self):self.tmp.cleanup()
 def post(self,name,path,v):
  c,csrf=self.clients[name];return c.post(path,json=v,headers={'X-CSRF-Token':csrf})
 def mutation(self,name,v):
  s=workflow.load();return self.post(name,'/api/workflow',dict({'role':'Eigenaar','revision':s['revision']},**v))
 def test_first_owner_activation_and_cookie_flags(self):
  empty=Path(self.tmp.name)/'activation';app=create_app(empty);c=app.test_client()
  before=app.accounts.path.read_bytes();r=c.post('/api/activate',json=dict(username='first-owner',password=PASSWORD,activation='invalid'));self.assertEqual(r.status_code,403)
  token=(empty/'owner-activation').read_text();r=c.post('/api/activate',json=dict(username='first-owner',password=PASSWORD,activation=token));self.assertEqual(r.status_code,200);self.assertFalse((empty/'owner-activation').exists())
  self.assertEqual(c.post('/api/activate',json=dict(username='other-owner',password=PASSWORD,activation=token)).status_code,403)
  r=c.post('/api/login',json=dict(username='first-owner',password=PASSWORD));cookie=r.headers['Set-Cookie'];self.assertIn('HttpOnly',cookie);self.assertIn('SameSite=Strict',cookie)
  self.assertEqual(c.post('/api/login',json=[],headers={'Origin':'http://evil.example'}).status_code,403)
  self.assertEqual(c.post('/api/login',json=[]).status_code,400)
  # Restore own test app globals after isolated activation app.
  workflow.FILE=self.state/'workflow.json'
 def test_authentication_and_direct_requests(self):
  c=self.app.test_client()
  for url in ['/api/dashboard','/api/workflow','/api/accounting-export','/api/users','/api/audit','/api/mechanic']:self.assertEqual(c.get(url).status_code,401,url)
  self.assertEqual(c.post('/api/workflow',json={}).status_code,403)
  self.assertEqual(self.clients['owner'][0].post('/api/users',json={}).status_code,403)
  c=self.clients['bram'][0]
  for url in ['/api/dashboard','/api/workflow','/api/accounting-export','/api/users','/api/audit','/api/config','/api/reconciliation']:self.assertEqual(c.get(url).status_code,403,url)
  before=(self.state/'workflow.json').read_bytes()
  for action in ['payment','tariff_save','credit','refund','invoice_rule','migration_commit','plan','tour_prepare']:
   self.assertEqual(self.mutation('bram',dict(action=action,job='W104',cents=100,role='Eigenaar')).status_code,403,action)
  self.assertEqual(self.post('bram','/api/users',dict(username='evil',password=PASSWORD,role='owner')).status_code,403)
  self.assertEqual(self.post('bram','/api/config',dict(order=[],visible=[])).status_code,403)
  self.assertEqual(self.mutation('bram',dict(action='repair',job='W103',hours=1,findings='TEST',materials='Geen')).status_code,403)
  self.assertEqual((self.state/'workflow.json').read_bytes(),before)
  my=c.get('/api/mechanic').json;self.assertNotIn('invoices',my);self.assertNotIn('tariffs',my)
  self.assertTrue(all('sales_invoice' not in o and 'cents' not in o for o in my['orders']))
 def test_audit_logout_revocation(self):
  r=self.mutation('bram',dict(action='note',job='W104',note='TEST eigen uitvoering',request_id='actor-1'));self.assertEqual(r.status_code,200,r.json)
  h=workflow.load()['history'][-1];self.assertEqual(h['actor']['username'],'bram');self.assertEqual(h['business_date'],'2026-10-26');self.assertIn('+00:00',h['at'])
  before=workflow.load()['revision'];r=self.mutation('bram',dict(action='note',job='W104',note='TEST eigen uitvoering',request_id='actor-1'));self.assertEqual(r.status_code,200);self.assertEqual(workflow.load()['revision'],before)
  c,csrf=self.clients['bram'];saved=c.get_cookie('server4_session').value
  self.assertEqual(self.post('bram','/api/logout',{}).status_code,200);c.set_cookie('server4_session',saved);self.assertEqual(c.get('/api/mechanic').status_code,401)
  c=self.clients['admin'][0];uid=self.app.accounts.current(self._sid(c))['id'];self.assertEqual(self.post('owner','/api/users/disable',dict(id=uid)).status_code,200);self.assertEqual(c.get('/api/dashboard').status_code,401)
 def _sid(self,c):
  with c.session_transaction() as s:return s['sid']
 def test_admin_boundaries_and_conflict(self):
  for action in ['credit','refund','payment_reverse','invoice_replace','tariff_save','invoice_rule','billing_save','invoice_revise','worktime','intake']:
   self.assertEqual(self.mutation('admin',dict(action=action,job='W104')).status_code,403,action)
  c=self.clients['owner'][0];rev=workflow.load()['revision'];r=self.post('owner','/api/workflow',dict(action='note',role='Bram',job='W104',note='TEST owner',revision=rev,request_id='conflict-1'));self.assertEqual(r.status_code,200,r.json)
  r=self.post('owner','/api/workflow',dict(action='note',role='Bram',job='W104',note='TEST stale',revision=rev,request_id='conflict-2'));self.assertEqual(r.status_code,400);self.assertIn('gewijzigd',r.json['error'])
 def test_real_roles_handoff_to_invoice_payment_close(self):
  def act(name,action,**v):
   r=self.mutation(name,dict(action=action,**v));self.assertEqual(r.status_code,200,(action,r.json));return r.json
  act('owner','intake',job='W104',customer='TEST rollenklant fictief',contact='TEST',scope='TEST rol-overdracht',priority='normaal',address='TEST straat',phone='0000000000',access='TEST')
  job=list(workflow.load()['operations']['orders'])[-1]
  act('owner','direct_agreement',job=job,who='TEST klant',date='2026-10-26',reference='TEST akkoord')
  act('owner','worktime',job=job,day='2026-11-06',employee='Bram',start='08:00',end='18:00')
  act('owner','plan',job=job,order=job,appointment='2026-11-06T09:00',employee='Bram',duration_minutes=60)
  act('owner','tariff_save',job=job,customer='TEST rollenklant fictief',rate_cents=6000,source='TEST eigenaarstarief')
  act('bram','finish',job=job,findings='TEST gereed',hours=1,materials='Geen materiaal')
  act('admin','invoice_draft',job=job,rate_cents=6000,source='TEST eigenaarstarief',due='2026-11-09')
  act('admin','invoice_final',job=job,confirmed=True);act('admin','invoice_send',job=job)
  act('admin','payment',job=job,cents=7260,date='2026-10-26',method='bank',reference='TEST betaald fictief')
  act('admin','admin_close',job=job)
  s=workflow.load();self.assertEqual(s['jobs'][job]['sales_invoice']['total_cents'],7260);self.assertTrue(s['jobs'][job]['administrative_closed'])
  self.assertEqual([h['actor']['username'] for h in s['history'] if h.get('job')==job][-6:],['bram','admin','admin','admin','admin','admin'])
  self.assertTrue(reconcile()['balanced'])
 def payload(self):return dict(batch_id='TEST_BATCH',customers=[dict(id='TEST_K',name='TEST klant fictief',address='TEST straat 1')],articles=[dict(id='TEST_A',name='TEST migratieartikel',unit_cents=1000,vat_percent=21,quantity=5,location='winkel')],balances=[dict(id='TEST_BEGIN',customer_id='TEST_K',date='2026-10-26',due='2026-11-26',net_cents=10000,vat_cents=2100)])
 def test_import_errors_duplicates_and_atomic_commit(self):
  payload=self.payload();before=(self.state/'workflow.json').read_bytes();r=self.post('owner','/api/migration/preview',payload);self.assertEqual(r.status_code,200,r.json);p=r.json;self.assertTrue(p['can_commit']);self.assertEqual(before,(self.state/'workflow.json').read_bytes())
  for field,value in [('quantity',-1),('unit_cents','10'),('vat_percent',9)]:
   bad=copy.deepcopy(payload);bad['articles'][0][field]=value;pbad=self.post('owner','/api/migration/preview',bad).json;self.assertTrue(pbad['errors']);self.assertEqual(pbad['errors'][0]['line'],1)
  bad=copy.deepcopy(payload);bad['balances'][0]['customer_id']='MISSING';self.assertTrue(self.post('owner','/api/migration/preview',bad).json['errors'])
  bad=copy.deepcopy(payload);bad['customers'].append(dict(bad['customers'][0]));self.assertTrue(self.post('owner','/api/migration/preview',bad).json['errors'])
  mutated=copy.deepcopy(payload);mutated['articles'][0]['quantity']=6
  r=self.mutation('owner',dict(action='migration_commit',payload=mutated,preview_digest=p['digest']));self.assertEqual(r.status_code,400);self.assertEqual(before,(self.state/'workflow.json').read_bytes())
  d0=self.clients['owner'][0].get('/api/dashboard').json
  r=self.mutation('owner',dict(action='migration_commit',payload=payload,preview_digest=p['digest'],request_id='import-1'));self.assertEqual(r.status_code,200,r.json)
  s=workflow.load();self.assertEqual(s['operations']['stock']['TEST migratieartikel @ winkel'],5);self.assertEqual(len(s['migration_history']),1)
  d1=self.clients['owner'][0].get('/api/dashboard').json;self.assertEqual(d1['open_cents']-d0['open_cents'],12100);self.assertEqual(d1['revenue_cents'],d0['revenue_cents']);self.assertEqual(d1['payments_cents'],d0['payments_cents'])
  p2=self.post('owner','/api/migration/preview',payload).json;self.assertTrue(p2['already_processed']);r=self.mutation('owner',dict(action='migration_commit',payload=payload,preview_digest=p2['digest'],request_id='import-2'));self.assertEqual(r.status_code,200,r.json);self.assertEqual(len(workflow.load()['migration_history']),1);self.assertEqual(workflow.load()['operations']['stock']['TEST migratieartikel @ winkel'],5)
  other=copy.deepcopy(payload);other['batch_id']='DIFFERENT';pd=self.post('owner','/api/migration/preview',other).json;self.assertFalse(pd['can_commit']);self.assertTrue(pd['duplicates'])
  result=reconcile();self.assertTrue(result['balanced'],result);self.assertEqual(result['opening_balances_cents'],12100);self.assertEqual(result['external_import'],'niet gevalideerd')
 def test_reconciliation_reports_both_source_gaps_and_tamper(self):
  r=self.clients['owner'][0].get('/api/reconciliation');self.assertEqual(r.status_code,200);self.assertTrue(r.json['balanced'],r.json);self.assertTrue(r.json['source_issues']);self.assertFalse(r.json['ready_for_external_import'])
  s=workflow.load();j=next(j for j in s['jobs'].values() if j.get('sales_invoice',{}).get('payments'));j['sales_invoice']['paid_cents']+=1;workflow.persist(s)
  r=reconcile();self.assertFalse(r['balanced']);self.assertTrue(r['differences'])
 def test_backup_restore_and_tamper(self):
  from recovery import backup,restore,external_copy
  payload=self.payload();preview=preview_import(workflow.load(),payload);r=self.mutation('owner',dict(action='migration_commit',payload=payload,preview_digest=preview['digest'],request_id='backup-import'));self.assertEqual(r.status_code,200,r.json)
  snap=Path(self.tmp.name)/'snapshot';manifest=backup(ROOT,self.state,snap)
  original=workflow.load();before=reconcile();root=Path(self.tmp.name)/'restored';root.mkdir();dest=Path(self.tmp.name)/'restored-state';dest.mkdir();(dest/'workflow.json').write_text('{"preserve":"newer"}')
  saved=Path(restore(root,dest,snap));self.assertEqual((saved/'state/workflow.json').read_text(),'{"preserve":"newer"}');self.assertEqual(json.loads((dest/'workflow.json').read_text()),original)
  for name,h in manifest.items():
   if name=='state/accounts.sqlite3':continue # restored sessions deliberately revoked
   p=(root if name.startswith('source/') else dest)/name.split('/',1)[1];self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),h)
  self.app=create_app(dest);c=self.app.test_client();self.assertEqual(c.get('/api/dashboard').status_code,401);self.assertEqual(c.post('/api/login',json=dict(username='owner',password=PASSWORD)).status_code,200)
  after=reconcile();self.assertEqual(before,dict(after,generated_at=before['generated_at']))
  (ROOT/'recovery-evidence.json').write_text(json.dumps(dict(result='PASS',environment='isolated temporary app and state',business_state_byte_identical=True,sections={k:hashlib.sha256(json.dumps(original.get(k),sort_keys=True).encode()).hexdigest() for k in ['jobs','history','operations','migration_history','customers','articles']},control_totals_before=before['expected'],control_totals_after=after['expected'],users_restored=3,old_sessions_revoked=True,source_files_verified=len(manifest)),indent=2))
  with sqlite3.connect(dest/'accounts.sqlite3') as d:self.assertEqual(d.execute('select count(*) from users').fetchone()[0],3)
  old=(dest/'workflow.json').read_bytes();(snap/'source/secure_app.py').write_text('TAMPERED')
  with self.assertRaises(ValueError):restore(root,dest,snap)
  self.assertEqual(old,(dest/'workflow.json').read_bytes())
  with self.assertRaises(ValueError):external_copy(snap,Path(self.tmp.name))
if __name__=='__main__':unittest.main(verbosity=2)
