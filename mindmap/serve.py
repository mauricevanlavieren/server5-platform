from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import os
import subprocess
from datetime import datetime, timezone
from urllib.parse import urlsplit

PUBLIC = Path(__file__).resolve().parent / 'public'
ALLOWED = {'/current-projects.html', '/current-projects.js', '/current-projects.json', '/', '/index.html', '/viewer.js', '/map.json', '/test-projects.html', '/test-projects.js', '/test-projects.json', '/dashboard.html', '/dashboard.js', '/dashboard-status.json', '/dashboard-next.html', '/dashboard-next.js'}
from dashboard_data import dashboard_status


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PUBLIC), **kwargs)
    def do_GET(self):
        if urlsplit(self.path).path == '/dashboard-status.json':
            payload = json.dumps(dashboard_status()).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        if urlsplit(self.path).path not in ALLOWED:
            self.send_error(404)
            return
        super().do_GET()
    def do_HEAD(self):
        if urlsplit(self.path).path not in ALLOWED:
            self.send_error(404)
            return
        super().do_HEAD()

ThreadingHTTPServer(('192.168.1.245', 8788), Handler).serve_forever()
