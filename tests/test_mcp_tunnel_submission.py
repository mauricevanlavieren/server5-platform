"""Real tunnel binary, local fake control plane, isolated adapter/DB; no Codex."""
import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
from pathlib import Path
import queue
import secrets
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest

SDK_AVAILABLE = importlib.util.find_spec('mcp') is not None
BINARY = Path.home() / '.local/bin/tunnel-client'
ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(SDK_AVAILABLE and BINARY.is_file() and socket.gethostname() == 'server5',
                     'Needs the isolated SDK and installed tunnel binary on server5')
class TunnelSubmissionTests(unittest.TestCase):
    def test_binary_forwarding_to_isolated_queue(self):
        sys.path.insert(0, str(ROOT / 'web'))
        from commandcenter import Store
        commands, responses = queue.Queue(), queue.Queue()

        class Mock(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def reply(self, code, body=None):
                raw = json.dumps(body).encode() if body is not None else b''
                try:
                    self.send_response(code)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', str(len(raw)))
                    self.end_headers(); self.wfile.write(raw)
                except OSError: pass
            def do_GET(self):
                if '/poll' in self.path:
                    try: command = commands.get(timeout=.2)
                    except queue.Empty: self.reply(204); return
                    self.reply(200, {'commands': [command]})
                else: self.reply(200, {'id': 'tunnel_' + '0' * 32, 'name': 'isolated fixture'})
            def do_POST(self):
                responses.put(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
                self.reply(200, {})

        server = ThreadingHTTPServer(('127.0.0.1', 0), Mock)
        server.daemon_threads = True
        thread = threading.Thread(target=server.serve_forever); thread.start()
        processes = []
        try:
            with tempfile.TemporaryDirectory(prefix='server5-mcp-isolated-') as temp:
                directory = Path(temp); state = directory / 'state'; store = Store(state)
                credential = directory / 'owner'; credential.write_text(secrets.token_urlsafe(48)); credential.chmod(0o600)
                header = directory / 'header'; header.write_text('Bearer ' + credential.read_text()); header.chmod(0o600)
                with socket.socket() as portfinder:
                    portfinder.bind(('127.0.0.1', 0)); port = portfinder.getsockname()[1]
                adapter = subprocess.Popen([sys.executable, str(ROOT / 'web/mcp_adapter.py'), '--state', str(state),
                    '--credential-file', str(credential), '--port', str(port), '--enable-start-task'],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env={'HOME':str(directory), 'PATH':'/usr/bin:/bin'})
                processes.append(adapter)
                for _ in range(100):
                    try:
                        with socket.create_connection(('127.0.0.1', port), timeout=.1): break
                    except OSError: time.sleep(.05)
                else: self.fail('Isolated adapter did not start')
                profile = directory / 'profile.yaml'
                profile.write_text(f'''config_version: 1
control_plane:
  base_url: http://127.0.0.1:{server.server_port}
  tunnel_id: tunnel_{'0' * 32}
  api_key: sk-local-fixture-not-a-platform-key
mcp:
  server_urls:
    - channel: main
      url: http://127.0.0.1:{port}/mcp
  extra_headers:
    Authorization: file:{header}
  discovery_extra_headers:
    Authorization: file:{header}
health:
  listen_addr: 127.0.0.1:0
log:
  level: warn
  format: json
  http_raw_unsafe: false
''')
                client = subprocess.Popen([str(BINARY), 'run', '--profile-file', str(profile)],
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                    env={'HOME':str(directory), 'PATH':'/usr/bin:/bin'})
                processes.append(client)
                time.sleep(.2)
                if client.poll() is not None:
                    self.fail('Local fixture client failed: ' + client.communicate()[0].replace(credential.read_text(), '[REDACTED]'))
                sequence = 0
                def rpc(method, params, headers=None):
                    nonlocal sequence
                    sequence += 1; request = 'fixture-' + str(sequence)
                    commands.put({'request_id': request, 'shard_token': 'synthetic-shard', 'command_type':'jsonrpc',
                        'channel':'main', 'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        'response_timeout':'10s', 'headers':headers or {},
                        'jsonrpc':{'jsonrpc':'2.0', 'id':sequence, 'method':method, 'params':params}})
                    response = responses.get(timeout=15)
                    self.assertEqual(response['request_id'], request)
                    return response
                def call(arguments, headers=None):
                    return rpc('tools/call', {'name':'start_task', 'arguments':arguments}, headers)
                args = {'instruction':'Geïsoleerde taak, geen worker', 'confirmed':True, 'request_id':'T' * 20}
                self.assertIn('result', rpc('initialize', {'protocolVersion':'2025-11-25', 'capabilities':{},
                    'clientInfo':{'name':'isolated test', 'version':'1'}})['resp_json'])
                tools = rpc('tools/list', {})['resp_json']['result']['tools']
                self.assertEqual({t['name'] for t in tools}, {'task_status','task_result','start_task'})
                self.assertIsNone(store.get(args['request_id']))
                self.assertTrue(call({**args, 'confirmed':False})['resp_json']['result']['isError'])
                self.assertIsNone(store.get(args['request_id']))
                first = call(args)['resp_json']['result']['structuredContent']
                again = call(args)['resp_json']['result']['structuredContent']
                self.assertEqual(first, again); self.assertEqual(first['status'], 'queued')
                denied = call({**args, 'request_id':'U' * 20}, {'authorization':['Bearer incorrect']})
                self.assertEqual(denied['resp_code'], 401)
                (state / 'mcp-start-task.disabled').touch()
                self.assertTrue(call({**args, 'request_id':'V' * 20})['resp_json']['result']['isError'])
                for name in ['task_status','task_result']:
                    result = rpc('tools/call', {'name':name, 'arguments':{'task_id':args['request_id']}})
                    self.assertFalse(result['resp_json']['result'].get('isError'))
                with store.db() as db:
                    self.assertEqual(db.execute('SELECT count(*) FROM tasks').fetchone()[0], 1)
                    self.assertEqual(db.execute('SELECT count(*) FROM events').fetchone()[0], 1)
        finally:
            for process in reversed(processes):
                process.terminate()
                try: process.wait(timeout=5)
                except subprocess.TimeoutExpired: process.kill(); process.wait()
                if process.stdout: process.stdout.close()
            server.shutdown(); thread.join(); server.server_close()
