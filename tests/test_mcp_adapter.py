"""Protocol tests use a temporary database, never a real Codex worker."""
import importlib.util
from pathlib import Path
import secrets
import sqlite3
import sys
import tempfile
import unittest

SDK_AVAILABLE = importlib.util.find_spec('mcp') is not None
if SDK_AVAILABLE:
    from starlette.testclient import TestClient
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'web'))
    from commandcenter import Store
    from mcp_adapter import create_app, ReadOnlyStore, load_token, SafeLogs


@unittest.skipUnless(SDK_AVAILABLE, 'Run with the isolated mcp-venv Python')
class MCPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(self.temp.name)
        self.tid = 'A' * 20
        self.store.submit('Testopdracht', self.tid)
        self.store.claim()
        self.token = secrets.token_urlsafe(48)
        self.headers = {'Host': '127.0.0.1:8796', 'Authorization': 'Bearer ' + self.token,
                        'Accept': 'application/json, text/event-stream'}
        self.client = TestClient(create_app(self.temp.name, self.token))
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.temp.cleanup()

    def rpc(self, method, params=None, headers=None):
        return self.client.post('/mcp', headers=headers or self.headers,
            json={'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params or {}})

    def call(self, name, args):
        return self.rpc('tools/call', {'name': name, 'arguments': args}).json()['result']

    def test_initialize_discovery_and_no_start(self):
        r = self.rpc('initialize', {'protocolVersion': '2025-11-25', 'capabilities': {},
                                  'clientInfo': {'name': 'test', 'version': '1'}})
        self.assertEqual(r.status_code, 200)
        self.assertIn('serverInfo', r.json()['result'])
        tools = self.rpc('tools/list').json()['result']['tools']
        self.assertEqual({t['name'] for t in tools}, {'task_status', 'task_result'})
        self.assertTrue(all(t['annotations']['readOnlyHint'] for t in tools))
        self.assertTrue(self.call('start_task', {'prompt': 'Geen uitvoering'})['isError'])
        self.assertEqual(self.store.get(self.tid)['status'], 'running')

    def test_auth_all_methods(self):
        for auth in [None, 'Bearer incorrect']:
            h = dict(self.headers)
            if auth is None: del h['Authorization']
            else: h['Authorization'] = auth
            for method in ['GET', 'POST', 'DELETE']:
                self.assertEqual(self.client.request(method, '/mcp', headers=h).status_code, 401)

    def test_origin_and_host(self):
        self.assertEqual(self.rpc('tools/list', headers={**self.headers, 'Origin': 'https://evil.invalid'}).status_code, 403)
        self.assertEqual(self.rpc('tools/list', headers={**self.headers, 'Host': 'evil.invalid'}).status_code, 421)

    def test_status_and_missing_invalid_ids(self):
        r = self.call('task_status', {'task_id': self.tid})
        self.assertEqual(r['structuredContent']['status'], 'running')
        self.assertNotIn('prompt', r['structuredContent'])
        for tid in ['x', "' OR 1=1 --", 'B' * 20]:
            self.assertTrue(self.call('task_status', {'task_id': tid})['isError'])

    def test_bounded_redacted_result(self):
        secret = 'sk-' + 'A' * 40
        # Seed unredacted legacy data deliberately; adapter must redact it too.
        with self.store.db() as db:
            db.execute('UPDATE tasks SET result=?,status=? WHERE id=?',
                       ('x' * 4090 + secret + self.token + 'z' * 9000, 'succeeded', self.tid))
        a = self.call('task_result', {'task_id': self.tid})['structuredContent']
        b = self.call('task_result', {'task_id': self.tid, 'offset': a['next_offset']})['structuredContent']
        self.assertLessEqual(len(a['result']), 4096)
        self.assertNotIn(secret, a['result'] + b['result'])
        self.assertNotIn(self.token, a['result'] + b['result'])
        self.assertTrue(a['complete'])
        for args in [{'limit': 4097}, {'offset': -1}, {'limit': True}]:
            self.assertTrue(self.call('task_result', {'task_id': self.tid, **args})['isError'])

    def test_read_only_and_restart_no_recovery(self):
        with ReadOnlyStore(self.temp.name).db() as db:
            with self.assertRaises(sqlite3.OperationalError):
                db.execute('DELETE FROM tasks')
        with TestClient(create_app(self.temp.name, self.token)) as restarted:
            r = restarted.post('/mcp', headers=self.headers,
                json={'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call',
                      'params': {'name': 'task_status', 'arguments': {'task_id': self.tid}}})
            self.assertEqual(r.json()['result']['structuredContent']['status'], 'running')
        self.assertEqual(self.store.get(self.tid)['status'], 'running')

    def test_request_body_limit(self):
        r = self.client.post('/mcp', headers=self.headers, content='x' * 17000)
        self.assertEqual(r.status_code, 413)

    def test_credentials_fail_closed(self):
        p = Path(self.temp.name) / 'token'
        p.write_text(self.token)
        p.chmod(0o600)
        self.assertEqual(load_token(p), self.token)
        p.chmod(0o644)
        with self.assertRaises(ValueError): load_token(p)
        link = Path(self.temp.name) / 'link'
        link.symlink_to(p)
        with self.assertRaises(OSError): load_token(link)


if __name__ == '__main__':
    unittest.main()
