import unittest,tempfile,copy,json
from pathlib import Path
import secure_app,workflow
ROOT=Path(__file__).parent
HOST='prognosis-energize-calzone.ngrok-free.dev'
class PublicAccess(unittest.TestCase):
 def setUp(self):
  secure_app.PUBLIC_DEMO_HOST=HOST;self.tmp=tempfile.TemporaryDirectory();self.state=Path(self.tmp.name);(self.state/'workflow.json').write_bytes((ROOT/'live-reference.json').read_bytes());self.app=secure_app.create_app(self.state);self.app.testing=True;self.c=self.app.test_client();self.base='https://'+HOST
 def tearDown(self):self.tmp.cleanup();secure_app.PUBLIC_DEMO_HOST=''
 def test_public_login_is_demo_only_and_cookie_secure(self):
  page=self.c.get('/login',base_url=self.base);self.assertEqual(page.status_code,200);self.assertIn(b'Toegang demo',page.data);self.assertNotIn(b'owner-activation',page.data);page.close()
  r=self.c.post('/api/demo-login',json={},base_url=self.base,headers={'Origin':self.base});self.assertEqual(r.status_code,200);self.assertEqual(r.json['user']['role'],'demo');self.assertIn('Secure;',r.headers['Set-Cookie']);self.assertIn('HttpOnly',r.headers['Set-Cookie']);self.assertEqual(self.c.get('/api/dashboard',base_url=self.base).status_code,200)
 def test_admin_paths_and_foreign_origins_are_denied(self):
  self.c.post('/api/demo-login',json={},base_url=self.base,headers={'Origin':self.base})
  for path in ['/api/users','/api/users/disable','/api/audit','/api/catalog','/api/migration/history','/api/activate','/api/login']:
   self.assertEqual(self.c.get(path,base_url=self.base).status_code,403,path)
   self.assertEqual(self.c.post(path,json={},base_url=self.base).status_code,403,path)
  self.assertEqual(self.c.post('/api/demo-login',json={},base_url=self.base,headers={'Origin':'https://evil.invalid'}).status_code,403)
  self.assertEqual(self.c.post('/api/demo-login',json={},base_url='https://unknown.invalid').status_code,403)
  self.assertEqual(self.c.post('/api/workflow',json={},base_url=self.base).status_code,403)
 def test_mutation_actor_and_logout_and_public_choice_restrictions(self):
  r=self.c.post('/api/demo-login',json={},base_url=self.base,headers={'Origin':self.base});csrf=r.json['csrf'];headers={'Origin':self.base,'X-CSRF-Token':csrf};rev=workflow.load()['revision']
  r=self.c.post('/api/workflow',json=dict(role='Bram',action='note',job='W104',revision=rev,note='TEST openbare fictieve demo',request_id='public-note-1'),base_url=self.base,headers=headers);self.assertEqual(r.status_code,200,r.json);self.assertEqual(workflow.load()['history'][-1]['actor']['role'],'demo')
  for a in ['trial_decisions','migration_commit']:self.assertEqual(self.c.post('/api/workflow',json=dict(action=a),base_url=self.base,headers=headers).status_code,403)
  old=self.c.get_cookie('server4_session',domain=HOST).value;self.assertEqual(self.c.post('/api/logout',json={},base_url=self.base,headers=headers).status_code,200);self.c.set_cookie('server4_session',old,domain=HOST);self.assertEqual(self.c.get('/api/dashboard',base_url=self.base).status_code,401)
 def test_private_owner_login_and_activation_still_available(self):
  self.app.accounts.create(dict(username='test-owner',password='Fictief-test-wachtwoord-2026',role='owner',employee=''));c=self.app.test_client();r=c.post('/api/login',json=dict(username='test-owner',password='Fictief-test-wachtwoord-2026'));self.assertEqual(r.status_code,200);self.assertEqual(c.get('/api/users').status_code,200)
if __name__=='__main__':unittest.main(verbosity=2)
