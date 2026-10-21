#!/usr/bin/env python3
"""Verify restored app/read-tools offline with synthetic owner auth; no worker."""
import contextlib
import http.client
import importlib
import json
import logging
from pathlib import Path
import secrets
import shutil
import sqlite3
import sys
import tempfile
import threading
from http.server import ThreadingHTTPServer
from unittest.mock import patch
from recovery import validate_into


def check(archive):
    logging.disable(logging.CRITICAL)
    with tempfile.TemporaryDirectory(prefix='server5-restored-app-') as temp:
        root = Path(temp); bundle = root / 'bundle'; bundle.mkdir(mode=0o700)
        manifest = validate_into(archive, bundle)
        sys.path.insert(0, str(bundle / 'project/web'))
        # Running main, a subprocess or a Worker is an explicit test failure.
        with patch('subprocess.Popen', side_effect=AssertionError('No subprocess in restore test')):
            mvp = importlib.import_module('commandcenter')
            with patch.object(mvp.Worker, 'start', side_effect=AssertionError('No worker in restore test')):
                state = root / 'isolated-state';state.mkdir(mode=0o700)
                shutil.copyfile(bundle / 'data/tasks.sqlite3', state / 'tasks.sqlite3')
                (state / 'tasks.sqlite3').chmod(0o600)
                app = mvp.App(state)  # Synthetic login only; never production auth.
                class Quiet(mvp.handler(app)):
                    def log_message(self, *args):pass
                server = ThreadingHTTPServer(('127.0.0.1', 0), Quiet)
                origin = 'http://127.0.0.1:' + str(server.server_port)
                app.origins = lambda: {origin}
                thread = threading.Thread(target=server.serve_forever);thread.start()
                try:
                    conn = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=3)
                    for url in ['/', '/app.js', '/style.css', '/api/health']:
                        conn.request('GET', url);resp=conn.getresponse();resp.read();assert resp.status==200
                    conn.request('GET', '/api/tasks');resp=conn.getresponse();resp.read();assert resp.status==401
                    password = (state/'login-password.txt').read_text().strip()
                    conn.request('POST','/api/login',json.dumps({'password':password}),
                                 {'Origin':origin,'Content-Type':'application/json'})
                    resp=conn.getresponse();resp.read();assert resp.status==200
                    cookie=resp.getheader('Set-Cookie').split(';')[0]
                    conn.request('GET','/api/tasks',headers={'Cookie':cookie})
                    resp=conn.getresponse();rows=json.loads(resp.read());assert resp.status==200
                    assert len(rows)==min(100,manifest['database']['tasks']['count'])
                    conn.close()
                finally:
                    server.shutdown();thread.join();server.server_close()
                adapter = importlib.import_module('mcp_adapter')
                from starlette.testclient import TestClient
                token = secrets.token_urlsafe(48)
                headers={'Authorization':'Bearer '+token,'Content-Type':'application/json',
                         'Accept':'application/json, text/event-stream','Host':'127.0.0.1:8796'}
                with TestClient(adapter.create_app(state,token,enable_start_task=True)) as client:
                    def rpc(method,params=None):
                        return client.post('/mcp',headers=headers,json={'jsonrpc':'2.0','id':1,'method':method,'params':params or {}})
                    result=rpc('initialize',{'protocolVersion':'2025-11-25','capabilities':{},'clientInfo':{'name':'isolated-restore','version':'1'}})
                    assert result.status_code==200 and 'result' in result.json()
                    tools=rpc('tools/list').json()['result']['tools']
                    assert {x['name'] for x in tools}=={'task_status','task_result','start_task'}
                    if rows:
                        for tool in ['task_status','task_result']:
                            result=rpc('tools/call',{'name':tool,'arguments':{'task_id':rows[0]['id']}}).json()['result']
                            assert not result.get('isError')
                    bad={**headers,'Authorization':'Bearer synthetic-invalid'}
                    assert client.post('/mcp',headers=bad,json={'jsonrpc':'2.0','id':1,'method':'tools/list'}).status_code==401
                with contextlib.closing(sqlite3.connect((state/'tasks.sqlite3').as_uri()+'?mode=ro',uri=True)) as db:
                    from recovery import db_summary
                    summary=db_summary(db)
                    assert summary['tasks']==manifest['database']['tasks']
                    assert summary['events']==manifest['database']['events']
    print(json.dumps({'isolated_app_restore':'passed','web_static_health_auth':True,'mcp_initialize_three_tools_reads_auth':True,
                      'task_event_content_unchanged':True,'workers_started':0,'production_credentials_used':False}))


if __name__=='__main__':
    try:check(Path(sys.argv[1]).resolve())
    except Exception:
        print('{"isolated_app_restore":"failed; inspect locally without exposing data"}')
        raise SystemExit(1)
