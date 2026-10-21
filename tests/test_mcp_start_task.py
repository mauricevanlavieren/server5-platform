"""All write cases use an isolated SQLite database, with no worker."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sqlite3
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import test_mcp_adapter as base
SDK_AVAILABLE = base.SDK_AVAILABLE
if SDK_AVAILABLE:
    from starlette.testclient import TestClient
    from mcp_adapter import create_app
    from commandcenter import Store


@unittest.skipUnless(SDK_AVAILABLE, 'Run with isolated mcp-venv Python')
class StartTaskTests(base.MCPTests):
    def setUp(self):
        super().setUp()
        self.client.__exit__(None, None, None)
        self.client = TestClient(create_app(self.temp.name, self.token, enable_start_task=True))
        self.client.__enter__()
        self.key = 'REQUEST_1234567890'

    def args(self, **overrides):
        return {'instruction': 'Alleen geïsoleerde testdata', 'confirmed': True,
                'request_id': self.key, **overrides}

    def rows(self, table='tasks'):
        with self.store.db() as db:
            return db.execute('SELECT count(*) FROM ' + table).fetchone()[0]

    def test_initialize_discovery_and_no_start(self):
        before = self.rows()
        self.assertEqual(self.rpc('initialize', {'protocolVersion': '2025-11-25', 'capabilities': {},
                         'clientInfo': {'name': 'test', 'version': '1'}}).status_code, 200)
        tools = self.rpc('tools/list').json()['result']['tools']
        self.assertEqual({t['name'] for t in tools}, {'task_status', 'task_result', 'start_task'})
        start = next(t for t in tools if t['name'] == 'start_task')
        self.assertFalse(start['annotations']['readOnlyHint'])
        self.assertTrue(start['annotations']['destructiveHint'])
        self.assertTrue(start['annotations']['idempotentHint'])
        self.assertEqual(set(start['inputSchema']['required']), {'instruction', 'confirmed', 'request_id'})
        self.assertEqual(self.rows(), before)

    def test_confirmed_must_be_strict_true(self):
        for value in [False, 'true', 1, None, 'false', 0]:
            self.assertTrue(self.call('start_task', self.args(confirmed=value))['isError'])
        missing = self.args(); del missing['confirmed']
        self.assertTrue(self.call('start_task', missing)['isError'])
        self.assertEqual(self.rows(), 1)
        self.assertEqual(self.rows('events'), 0)

    def test_offer_audit_and_idempotent_replay(self):
        a = self.call('start_task', self.args())['structuredContent']
        b = self.call('start_task', self.args())['structuredContent']
        self.assertEqual(a, b)
        self.assertEqual(a['task_id'], self.key)
        self.assertEqual(a['status'], 'queued')
        self.assertTrue(a['queued'])
        self.assertEqual(self.rows(), 2)
        self.assertEqual(self.rows('events'), 1)
        with self.store.db() as db:
            audit = db.execute('SELECT text FROM events WHERE task=?', (self.key,)).fetchone()[0]
        self.assertIn('confirmed=true', audit)
        self.assertNotIn(self.args()['instruction'], audit)

    def test_conflicting_id_refused(self):
        self.call('start_task', self.args())
        self.assertTrue(self.call('start_task', self.args(instruction='Andere opdracht'))['isError'])
        self.assertEqual(self.rows(), 2)

    def test_invalid_input_and_secrets_refused(self):
        for values in [{'instruction': ''}, {'instruction': '  '}, {'instruction': 'x' * 8001},
                       {'instruction': 42}, {'instruction': self.token},
                       {'instruction': 'sk-' + 'A' * 40}, {'request_id': 'x'},
                       {'request_id': 'x' * 81}, {'request_id': '../' + 'x' * 20},
                       {'request_id': self.token}, {'request_id': 'sk-' + 'A' * 40}]:
            self.assertTrue(self.call('start_task', self.args(**values))['isError'])
        self.assertEqual(self.rows(), 1)

    def test_authentication_precedes_write(self):
        headers = {k: v for k, v in self.headers.items() if k != 'Authorization'}
        self.assertEqual(self.rpc('tools/call', {'name': 'start_task', 'arguments': self.args()}, headers).status_code, 401)
        self.assertEqual(self.rows(), 1)

    def test_stop_marker_immediate_and_read_tools_preserved(self):
        marker = Path(self.temp.name) / 'mcp-start-task.disabled'
        marker.touch()
        self.assertTrue(self.call('start_task', self.args())['isError'])
        self.assertEqual(self.rows(), 1)
        self.assertFalse(self.call('task_status', {'task_id': self.tid})['isError'])
        marker.unlink()
        self.assertFalse(self.call('start_task', self.args())['isError'])

    def test_audit_failure_rolls_back_submission(self):
        with patch.object(Store, 'event', side_effect=sqlite3.OperationalError('synthetic audit failure')):
            self.assertTrue(self.call('start_task', self.args())['isError'])
        self.assertIsNone(self.store.get(self.key))

    def test_existing_queue_limit_preserved(self):
        for i in range(19): self.store.submit('Test', 'F' * 18 + f'{i:02}')
        self.assertTrue(self.call('start_task', self.args())['isError'])
        self.assertEqual(self.rows(), 20)

    def test_concurrent_duplicate_requests(self):
        def offer(_): return self.call('start_task', self.args())
        with ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(offer, range(6)))
        self.assertTrue(all(not r.get('isError') for r in results))
        self.assertEqual(self.rows(), 2)
        self.assertEqual(self.rows('events'), 1)

    def test_replay_after_reinitialization_does_not_requeue_running(self):
        self.call('start_task', self.args())
        with self.store.db() as db: db.execute("UPDATE tasks SET status='running' WHERE id=?", (self.key,))
        with TestClient(create_app(self.temp.name, self.token, enable_start_task=True)) as restarted:
            r = restarted.post('/mcp', headers=self.headers, json={'jsonrpc': '2.0', 'id': 9,
                'method': 'tools/call', 'params': {'name': 'start_task', 'arguments': self.args()}})
        data = r.json()['result']['structuredContent']
        self.assertEqual(data['status'], 'running')
        self.assertFalse(data['queued'])
        self.assertEqual(self.rows('events'), 1)

    def test_default_remains_read_only(self):
        with TestClient(create_app(self.temp.name, self.token)) as off:
            response = off.post('/mcp', headers=self.headers, json={'jsonrpc': '2.0', 'id': 10, 'method': 'tools/list'})
        self.assertEqual({t['name'] for t in response.json()['result']['tools']}, {'task_status', 'task_result'})
