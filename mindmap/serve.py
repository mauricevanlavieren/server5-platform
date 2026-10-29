from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import os
import subprocess
from datetime import datetime, timezone
from urllib.parse import urlsplit
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import re
import sqlite3

PUBLIC = Path(__file__).resolve().parent / 'public'
ALLOWED = {'/current-projects.html', '/current-projects.js', '/current-projects.json', '/', '/index.html', '/viewer.js', '/map.json', '/test-projects.html', '/test-projects.js', '/test-projects.json', '/dashboard.html', '/dashboard.js', '/dashboard-status.json', '/dashboard-next.html', '/dashboard-next.js', '/cockpit.html'}
from dashboard_data import dashboard_status, fleet_status
import sys
sys.path.insert(0, str(PUBLIC.parents[1] / "web"))


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PUBLIC), **kwargs)
    def do_GET(self):
        if self._proxy_commandcenter():
            return
        if urlsplit(self.path).path == '/dashboard-fleet-status.json':
            payload = json.dumps(fleet_status()).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        if urlsplit(self.path).path == '/dashboard-status.json':
            payload = json.dumps(dashboard_status()).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        if urlsplit(self.path).path == '/dashboard-tasks.json':
            # Read the existing broker database in read-only mode. Prompts and
            # results may contain private text, so expose only task metadata.
            db_path = Path.home() / '.local/state/server5-commandcenter/mvp/tasks.sqlite3'
            try:
                with sqlite3.connect(db_path.as_uri() + '?mode=ro', uri=True, timeout=1) as db:
                    db.execute('PRAGMA query_only=ON')
                    rows = db.execute('SELECT id,status,created,started,finished FROM tasks ORDER BY created DESC LIMIT 100').fetchall()
                tasks = [dict(id=r[0], status=r[1], created=r[2], started=r[3], finished=r[4]) for r in rows]
                payload = json.dumps(tasks, ensure_ascii=False).encode()
                code = 200
            except (sqlite3.Error, OSError, ValueError):
                payload = b'{"error":"Taakstatus tijdelijk niet beschikbaar"}'
                code = 503
            self.send_response(code)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(payload)))
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(payload)
            return
        if urlsplit(self.path).path not in ALLOWED:
            self.send_error(404)
            return
        super().do_GET()
    def do_POST(self):
        if self._proxy_commandcenter():
            return
        from current_projects_clear import clear
        path = urlsplit(self.path).path
        def json_response(status, payload):
            body = json.dumps(payload, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        if path == "/dashboard-fleet-control":
            expected = f"http://{self.headers.get('Host', '')}"
            if self.headers.get("Origin") != expected or self.headers.get("Host") != "192.168.1.245:8788":
                json_response(403, {"status": "rejected", "message": "Dashboardactie geweigerd: ongeldige dashboardherkomst."}); return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if self.headers.get("Content-Type", "").split(";")[0] != "application/json" or not 0 < size <= 1024:
                    raise ValueError("JSON vereist")
                data = json.loads(self.rfile.read(size))
                if not isinstance(data, dict) or set(data) != {"action", "target"}:
                    raise ValueError("Ongeldige opdracht")
                action, target = data["action"], data["target"]
                if action not in {"wake", "poweroff"} or target not in {"server1", "server2", "server3", "server4", "server6"}:
                    json_response(400, {"status": "rejected", "target": data.get("target"),
                                        "action": data.get("action"),
                                        "message": "Dashboardactie geweigerd: doel of actie niet toegestaan. Server5 kan nooit via deze bediening worden aangestuurd."}); return
            except (ValueError, TypeError, json.JSONDecodeError):
                json_response(400, {"status": "rejected", "message": "Ongeldige dashboardopdracht; geen beheeractie uitgevoerd."}); return
            script = PUBLIC.parents[1] / "scripts/server5-fleet-power"
            timeout = 450 if action == "wake" else 30
            try:
                result = subprocess.run([str(script), action, target], cwd=PUBLIC.parents[1],
                                        capture_output=True, text=True, timeout=timeout, check=False)
                output = (result.stdout + result.stderr).strip()
                if result.returncode == 0:
                    if action == "wake":
                        message = f"{target}: SSH is bereikbaar; AAN bevestigd."
                    else:
                        message = f"{target}: uitschakelopdracht is uitgevoerd; live status wordt bijgewerkt."
                    status, code = "succeeded", 200
                else:
                    message = output[-1200:] or f"Beheeractie stopte met code {result.returncode}."
                    status, code = "failed", 502
            except subprocess.TimeoutExpired:
                status, code, message = "timeout", 504, f"{target}: geen bevestiging binnen de ingestelde tijd; controleer de live status."
            json_response(code, {"status": status, "target": target, "action": action, "message": message}); return
        if path != "/current-projects.json":
            self.send_error(404); return
        if self.headers.get("Host") != "192.168.1.245:8788" or self.headers.get("Origin") != "http://192.168.1.245:8788":
            self.send_error(403); return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if self.headers.get("Content-Type", "").split(";")[0] != "application/json" or not 0 < size <= 1024:
                raise ValueError("JSON vereist")
            payload = json.dumps(clear(PUBLIC.parents[1], json.loads(self.rfile.read(size)))).encode()
        except (ValueError, TypeError):
            self.send_error(400); return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _proxy_commandcenter(self):
        """Expose only the existing owner task API through this same-origin dashboard."""
        path = urlsplit(self.path).path
        allowed = (
            path in {'/api/login', '/api/session', '/api/tasks'} or
            re.fullmatch(r'/api/tasks/[A-Za-z0-9_-]{16,80}(?:/events)?', path)
        )
        if not allowed:
            return False
        if self.command not in {'GET', 'POST'} or (self.command == 'GET' and path == '/api/tasks' and self.path != path):
            self.send_error(405)
            return True
        length = int(self.headers.get('Content-Length', '0'))
        if length > 16384:
            self.send_error(413)
            return True
        body = self.rfile.read(length) if self.command == 'POST' and length else None
        headers = {
            'Host': '127.0.0.1:8795',
            'Origin': 'http://127.0.0.1:8795',
            'Accept': 'application/json',
        }
        for name in ('Content-Type', 'Cookie', 'X-CSRF-Token'):
            if self.headers.get(name):
                headers[name] = self.headers[name]
        request = Request('http://127.0.0.1:8795' + self.path, data=body,
                          headers=headers, method=self.command)
        try:
            response = urlopen(request, timeout=8)
            code, payload = response.status, response.read(1_000_001)
            extra = response.headers.get('Set-Cookie')
        except HTTPError as exc:
            code, payload = exc.code, exc.read(1_000_001)
            extra = exc.headers.get('Set-Cookie')
        except (URLError, TimeoutError, OSError) as exc:
            payload = json.dumps({'error': f'Commandcenter niet bereikbaar: {type(exc).__name__}'}).encode()
            code, extra = 502, None
        if len(payload) > 1_000_000:
            payload = json.dumps({'error': 'Commandcenter-antwoord te groot'}).encode()
            code, extra = 502, None
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        if extra:
            self.send_header('Set-Cookie', extra)
        self.end_headers()
        self.wfile.write(payload)
        return True

    def do_HEAD(self):
        if urlsplit(self.path).path not in ALLOWED:
            self.send_error(404)
            return
        super().do_HEAD()

ThreadingHTTPServer(('192.168.1.245', 8788), Handler).serve_forever()
