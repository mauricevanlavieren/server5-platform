import unittest,json,tempfile,sqlite3,copy
from pathlib import Path
from secure_app import create_app
from delivery import CASES
import workflow
ROOT=Path(__file__).parent
class DeliveryTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.state=Path(self.tmp.name);(self.state/'workflow.json').write_bytes((ROOT/'live-reference.json').read_bytes());self.app=create_app(self.state);self.app.testing=True;self.clients={}
  for name,role,employee in [('owner','owner',''),('mechanic','mechanic','Bram'),('shop','shop',''),('administration','administration','')]:
   self.app.accounts.create(dict(username='test-'+name,password='Fictief-test-wachtwoord-2026',role=role,employee=employee));c=self.app.test_client();r=c.post('/api/login',json=dict(username='test-'+name,password='Fictief-test-wachtwoord-2026'));self.clients[name]=(c,r.json['csrf'])
  c=self.app.test_client();r=c.post('/api/demo-login',json={});self.clients['demo']=(c,r.json['csrf'])
 def tearDown(self):self.tmp.cleanup()
 def post(self,role,path,v):return self.clients[role][0].post(path,json=v,headers={'X-CSRF-Token':self.clients[role][1]})
 def act(self,role,action,**v):return self.post(role,'/api/workflow',dict(role='Eigenaar',action=action,revision=workflow.load()['revision'],**v))
 def test_owner_decisions_are_explicit_versioned_and_restricted(self):
  before=workflow.load();r=self.clients['demo'][0].get('/api/trial');self.assertEqual(r.status_code,200);self.assertEqual(r.json['decisions'],{});self.assertEqual(r.json['external_import'],'niet gevalideerd')
  for role in ['demo','shop','mechanic','administration']:self.assertEqual(self.act(role,'trial_decisions',values={'one_time_cost':'TEST'},reference='TEST').status_code,403)
  r=self.act('owner','trial_decisions',values={'trial_start':'2026-11-03','trial_end':'2026-11-05','one_time_cost':'TEST €100 excl btw, geen aanbod','support_contact':'TEST begeleider (fictief)'},reference='TEST conceptkeuze');self.assertEqual(r.status_code,200,r.json)
  trial=workflow.load()['trial'];self.assertEqual(trial['decisions']['one_time_cost']['actor']['role'],'owner');self.assertNotIn('recurring_cost',trial['decisions']);self.assertEqual(len(trial['decision_history']),1)
  self.assertEqual(self.act('owner','trial_decisions',values={'trial_end':'2026-01-01'},reference='TEST').status_code,400)
  self.assertEqual(self.act('owner','trial_decisions',values={'unknown':'TEST'},reference='TEST').status_code,400)
  self.assertEqual(workflow.load()['operations'],before['operations'])
 def test_individual_acceptance_and_demo_distinction(self):
  for case in CASES:
   steps=[k for k,_ in CASES[case]['steps']]
   r=self.act('demo','trial_accept',case_id=case,outcome='passed',steps=steps,note='TEST demonstratie');self.assertEqual(r.status_code,200,r.json)
  data=self.clients['demo'][0].get('/api/trial').json;self.assertFalse(any(data['staff_self_reported'].values()))
  self.assertEqual(self.act('shop','trial_accept',case_id='mechanic',outcome='passed',steps=[],note='TEST').status_code,403)
  self.assertEqual(self.act('shop','trial_accept',case_id='shop',outcome='passed',steps=[],note='TEST').status_code,400)
  for role in CASES:
   r=self.act(role,'trial_accept',case_id=role,outcome='passed',steps=[k for k,_ in CASES[role]['steps']],note='TEST eigen gecontroleerde route');self.assertEqual(r.status_code,200,r.json)
  data=self.clients['demo'][0].get('/api/trial').json;self.assertTrue(all(data['staff_self_reported'].values()));self.assertEqual(len(data['acceptance']),6)
  v=dict(role='Eigenaar',action='trial_accept',case_id='shop',outcome='blocked',steps=[],note='TEST dubbelklik',revision=workflow.load()['revision'],request_id='accept-repeat')
  r=self.post('shop','/api/workflow',v);self.assertEqual(r.status_code,200);revision=workflow.load()['revision'];r=self.post('shop','/api/workflow',v);self.assertEqual(r.status_code,200);self.assertEqual(workflow.load()['revision'],revision)
 def test_shop_routes_money_inventory_and_access(self):
  r=self.act('owner','stock_receive',job='W104',part='TEST Winkelproef',location='winkel',quantity=5,source='TEST voorraad');self.assertEqual(r.status_code,200,r.json)
  s=workflow.load();from pilot import reconcile
  before=reconcile()['expected'];r=self.act('shop','sale',job='W104',part='TEST Winkelproef',location='winkel',quantity=2,unit_cents=1000,source='TEST prijsbron');self.assertEqual(r.status_code,200,r.json);self.assertNotIn('jobs',r.json)
  sale=workflow.load()['operations']['sales'];ident=list(sale)[-1];r=self.act('shop','sale_return',job='W104',sale=ident,quantity=1,date='2026-10-26',reason='TEST deelretour');self.assertEqual(r.status_code,200,r.json)
  self.assertEqual(workflow.load()['operations']['stock']['TEST Winkelproef @ winkel'],4);after=reconcile();self.assertTrue(after['balanced']);self.assertEqual(after['expected']['net_received_cents']-before['net_received_cents'],1210);self.assertEqual(after['expected']['revenue_cents']-before['revenue_cents'],1000)
  for path in ['/api/dashboard','/api/workflow','/api/users','/api/accounting-export','/api/reconciliation','/api/trial/accounting']:self.assertEqual(self.clients['shop'][0].get(path).status_code,403,path)
  for action in ['payment','tariff_save','credit','stock_receive','migration_commit']:self.assertEqual(self.act('shop',action,job='W104').status_code,403,action)
  page=self.clients['shop'][0].get('/proefvoorstel');self.assertEqual(page.status_code,200);page.close()
 def test_administration_accepts_empty_material_controls_but_not_price_changes(self):
  r=self.act('owner','intake',job='W104',customer='TEST leeg materiaal fictief',contact='TEST',scope='TEST',priority='normaal',address='TEST',phone='0000000000',access='TEST');self.assertEqual(r.status_code,200)
  job=list(workflow.load()['operations']['orders'])[-1]
  self.act('owner','direct_agreement',job=job,who='TEST',date='2026-10-26',reference='TEST')
  self.act('owner','worktime',job=job,day='2026-11-06',employee='Bram',start='08:00',end='18:00')
  self.act('owner','plan',job=job,order=job,employee='Bram',appointment='2026-11-06T09:00',duration_minutes=60)
  self.act('owner','tariff_save',job=job,customer='TEST leeg materiaal fictief',rate_cents=6000,source='TEST prijsbron')
  r=self.act('mechanic','finish',job=job,findings='TEST',hours=1,materials='Geen materiaal');self.assertEqual(r.status_code,200,r.json)
  r=self.act('administration','invoice_draft',job=job,rate_cents=6000,source='TEST prijsbron',due='2026-11-09',material_quantity=1,material_unit_cents=1000,material_source='TEST onbevoegde prijs');self.assertEqual(r.status_code,403)
  r=self.act('administration','invoice_draft',job=job,rate_cents=6000,source='TEST prijsbron',due='2026-11-09',material_prices={},material_quantity=0,material_unit_cents=0,material_source='');self.assertEqual(r.status_code,200,r.json);self.assertEqual(workflow.load()['jobs'][job]['sales_invoice']['total_cents'],7260)
 def test_accounting_preparation_does_not_claim_external_validation(self):
  before=(self.state/'workflow.json').read_bytes();r=self.clients['administration'][0].get('/api/trial/accounting');self.assertEqual(r.status_code,200);self.assertTrue(r.json['balanced']);self.assertEqual(r.json['external_import'],'niet gevalideerd');self.assertEqual(len(r.json['source_issues']),19);self.assertTrue(r.json['remaining_manual_work']);self.assertEqual(before,(self.state/'workflow.json').read_bytes())
if __name__=='__main__':unittest.main(verbosity=2)
