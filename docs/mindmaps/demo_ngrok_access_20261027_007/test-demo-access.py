import unittest,tempfile,json,sqlite3
from pathlib import Path
from secure_app import create_app
import workflow
ROOT=Path(__file__).parent
class DemoAccess(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.state=Path(self.tmp.name);(self.state/'workflow.json').write_bytes((ROOT/'live-reference.json').read_bytes());self.app=create_app(self.state);self.app.testing=True;self.c=self.app.test_client()
 def tearDown(self):self.tmp.cleanup()
 def enter(self):
  r=self.c.post('/api/demo-login',json={'role':'owner'});self.assertEqual(r.status_code,200,r.json);self.assertEqual(r.json['user']['role'],'demo');return r.json['csrf']
 def test_entry_mutation_replay_and_revoked_logout(self):
  self.assertEqual(self.c.get('/api/dashboard').status_code,401);csrf=self.enter();self.assertEqual(self.c.get('/api/dashboard').status_code,200)
  original=workflow.load();v=dict(role='Bram',action='note',job='W104',note='TEST demobezoeker',revision=original['revision'],request_id='demo-note-1');r=self.c.post('/api/workflow',json=v,headers={'X-CSRF-Token':csrf});self.assertEqual(r.status_code,200,r.json)
  h=workflow.load()['history'][-1];self.assertEqual(h['actor']['role'],'demo');self.assertIsNone(h['actor']['id']);rev=workflow.load()['revision'];self.assertEqual(self.c.post('/api/workflow',json=v,headers={'X-CSRF-Token':csrf}).status_code,200);self.assertEqual(workflow.load()['revision'],rev)
  old=self.c.get_cookie('server4_session').value;self.assertEqual(self.c.post('/api/logout',json={},headers={'X-CSRF-Token':csrf}).status_code,200);self.c.set_cookie('server4_session',old);self.assertEqual(self.c.get('/api/dashboard').status_code,401)
  with sqlite3.connect(self.app.accounts.path) as d:self.assertEqual(d.execute('select count(*) from users').fetchone()[0],0)
 def test_demo_cannot_manage_accounts_or_import_and_csrf_remains(self):
  csrf=self.enter();headers={'X-CSRF-Token':csrf};before=(self.state/'workflow.json').read_bytes()
  for path in ['/api/users','/api/audit','/api/catalog','/api/migration/history']:self.assertEqual(self.c.get(path).status_code,403,path)
  for path in ['/api/users','/api/users/disable','/api/migration/preview','/api/config']:self.assertEqual(self.c.post(path,json={},headers=headers).status_code,403,path)
  r=self.c.post('/api/workflow',json=dict(role='Eigenaar',action='migration_commit',revision=workflow.load()['revision']),headers=headers);self.assertEqual(r.status_code,403)
  self.assertEqual(self.c.post('/api/workflow',json={}).status_code,403);self.assertEqual(self.c.post('/api/demo-login',json={},headers={'Origin':'https://example.com'}).status_code,403)
  self.assertEqual(self.c.post('/api/demo-login',data='x',content_type='text/plain').status_code,415);self.assertEqual(self.c.get('/api/demo-login').status_code,405)
  self.assertEqual(before,(self.state/'workflow.json').read_bytes());self.assertTrue((self.state/'owner-activation').exists())
 def test_real_account_login_remains_and_demo_expires(self):
  self.app.accounts.create(dict(username='test-owner',password='Fictief-test-wachtwoord-2026',role='owner',employee=''));self.enter();old=self.c.get_cookie('server4_session').value
  r=self.c.post('/api/login',json=dict(username='test-owner',password='Fictief-test-wachtwoord-2026'));self.assertEqual(r.status_code,200);self.assertEqual(self.c.get('/api/users').status_code,200)
  other=self.app.test_client();other.set_cookie('server4_session',old);self.assertEqual(other.get('/api/dashboard').status_code,401)
  self.enter()
  with sqlite3.connect(self.app.accounts.path) as d:d.execute('update sessions set expires=0 where user_id is null')
  self.assertEqual(self.c.get('/api/dashboard').status_code,401)
if __name__=='__main__':unittest.main(verbosity=2)
