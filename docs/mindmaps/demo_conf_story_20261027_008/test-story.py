import unittest,tempfile,json,copy,hashlib,sqlite3
from pathlib import Path
from unittest.mock import patch
import workflow,demo_story,secure_app
ROOT=Path(__file__).parent
class Story(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.state=Path(self.tmp.name);(self.state/'workflow.json').write_text(json.dumps(demo_story.standard(1,dict(id=None,username='TEST fixture',role='system'))));self.app=secure_app.create_app(self.state);self.app.testing=True;self.clients={}
  for name,role,employee in [('owner','owner',''),('mechanic','mechanic','Bram'),('shop','shop',''),('admin','administration','')]:
   self.app.accounts.create(dict(username='test-'+name,password='Fictief-test-wachtwoord-2026',role=role,employee=employee));c=self.app.test_client();r=c.post('/api/login',json=dict(username='test-'+name,password='Fictief-test-wachtwoord-2026'));self.clients[name]=(c,r.json['csrf'])
  c=self.app.test_client();r=c.post('/api/demo-login',json={});self.clients['demo']=(c,r.json['csrf'])
 def tearDown(self):self.tmp.cleanup()
 def post(self,name,path,v):return self.clients[name][0].post(path,json=v,headers={'X-CSRF-Token':self.clients[name][1]})
 def test_append_seed_preserves_all_existing_facts_and_is_idempotent(self):
  s=workflow.load();s.pop('demo_scenario');old=copy.deepcopy(s);new=demo_story.add_stories(s,dict(role='system',username='TEST'))
  third=new['demo_scenario']['featured'][2];missing=new['jobs'][third]['waiting_part']['part'];self.assertNotIn(missing+' @ winkel',new['operations']['stock'])
  self.assertEqual(s,old);self.assertEqual(new['revision'],old['revision']+1)
  for ident,order in old['operations']['orders'].items():self.assertEqual(new['operations']['orders'][ident],order)
  for ident,job in old['jobs'].items():self.assertEqual(new['jobs'][ident],job)
  for key,qty in old['operations']['stock'].items():self.assertEqual(new['operations']['stock'][key],qty)
  self.assertEqual(new['history'][:-1],old['history']);self.assertEqual(demo_story.add_stories(new),new)
  from pilot import reconcile
  workflow.persist(new);self.assertTrue(reconcile()['balanced'])
 def test_reset_archives_old_data_and_preserves_accounts_choices_and_receipts(self):
  s=workflow.load();s['trial']=dict(decisions={'pilot_lead':{'value':'TEST eigenaar'}});s['operations']['stock']['TEST eigen artikel @ winkel']=19;s['history'].append(dict(role='Eigenaar',action='note',job='W104',at='2026-10-27T12:00:00+00:00',sequence=99,details={'note':'TEST bewaar historie'}));workflow.persist(s)
  before=workflow.load();r=self.post('owner','/api/demo/reset',dict(revision=before['revision'],request_id='reset-1'));self.assertEqual(r.status_code,200,r.json);new=workflow.load();archive=json.loads((self.state/'demo-reset-archives'/(r.json['archive_id']+'.json')).read_text());self.assertEqual(archive['state'],before);self.assertEqual(new['revision'],before['revision']+1);self.assertNotEqual(new['demo_scenario']['epoch'],before['demo_scenario']['epoch']);self.assertEqual(new['trial']['decisions'],before['trial']['decisions'])
  with sqlite3.connect(self.app.accounts.path) as d:self.assertEqual(d.execute('select count(*) from users').fetchone()[0],4)
  r2=self.post('owner','/api/demo/reset',dict(revision=before['revision'],request_id='reset-1'));self.assertEqual(r2.status_code,200);self.assertTrue(r2.json['replayed']);self.assertEqual(workflow.load(),new);self.assertEqual(len(list((self.state/'demo-reset-archives').glob('*.json'))),1)
  # Mutations submitted before reset cannot overwrite the new standard.
  r=self.post('demo','/api/workflow',dict(role='Bram',action='note',job='W104',note='TEST stale',revision=before['revision']));self.assertEqual(r.status_code,400)
 def test_reset_rights_and_archive_failure_are_safe(self):
  before=(self.state/'workflow.json').read_bytes();revision=workflow.load()['revision']
  for role in ['demo','admin','mechanic','shop']:
   self.assertEqual(self.post(role,'/api/demo/reset',dict(revision=revision,request_id='denied')).status_code,403,role)
  with patch('demo_story.tempfile.mkstemp',side_effect=OSError('TEST archive storage failure')):
   r=self.post('owner','/api/demo/reset',dict(revision=revision,request_id='failed-reset'));self.assertEqual(r.status_code,503)
  self.assertEqual((self.state/'workflow.json').read_bytes(),before)
  secure_app.PUBLIC_DEMO_HOST='demo.invalid'
  try:self.assertEqual(self.app.test_client().post('/api/demo/reset',base_url='https://demo.invalid',json={}).status_code,403)
  finally:secure_app.PUBLIC_DEMO_HOST=''
 def test_reset_archive_is_in_backup_and_isolated_restore(self):
  from recovery import backup,restore
  old=workflow.load();r=self.post('owner','/api/demo/reset',dict(revision=old['revision'],request_id='restore-proof'));self.assertEqual(r.status_code,200)
  snapshot=Path(self.tmp.name)/'snapshot';manifest=backup(ROOT,self.state,snapshot);archivename='state/demo-reset-archives/'+r.json['archive_id']+'.json';self.assertIn(archivename,manifest)
  app=Path(self.tmp.name)/'restored-app';state=Path(self.tmp.name)/'restored-state';app.mkdir();state.mkdir();restore(app,state,snapshot)
  self.assertEqual(json.loads((state/'demo-reset-archives'/(r.json['archive_id']+'.json')).read_text())['state'],old)
  self.assertEqual(json.loads((state/'workflow.json').read_text()),workflow.load())
 def test_friendly_input_errors_no_raw_server_details(self):
  before=(self.state/'workflow.json').read_bytes();rev=workflow.load()['revision']
  r=self.post('demo','/api/workflow',dict(role='Eigenaar',action='intake',job='W104',revision=rev,customer='TEST',scope='TEST',priority='normaal',contact='TEST',address='TEST straat',phone='letters',access='TEST'));self.assertEqual(r.status_code,400);self.assertIn('telefoonnummer',r.json['error'])
  r=self.post('demo','/api/workflow',dict(role='Eigenaar',action='plan',job='W104',order='W104',revision=rev,appointment='letters',employee='Bram',duration_minutes=60));self.assertEqual(r.status_code,400);self.assertIn('datum',r.json['error']);self.assertNotIn('strptime',r.json['error'])
  self.assertEqual((self.state/'workflow.json').read_bytes(),before)
if __name__=='__main__':unittest.main(verbosity=2)
