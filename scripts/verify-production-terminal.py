#!/usr/bin/env python3
"""Read-only foreground host check AFTER worker exit; never submits a task."""
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
TASK = 'mindmap-production-yellow-audit-20261023-01'

def walk(node):
    yield node
    for child in node.get('children', []):
        yield from walk(child)

def main():
    deadline = time.monotonic() + 45
    dbpath = Path.home() / '.local/state/server5-commandcenter/mvp/tasks.sqlite3'
    with sqlite3.connect(dbpath.as_uri() + '?mode=ro', uri=True) as db:
        while time.monotonic() < deadline:
            status = db.execute('SELECT status FROM tasks WHERE id=?', (TASK,)).fetchone()
            with urllib.request.urlopen(urllib.request.Request(
                'http://192.168.1.245:8788/map.json', headers={'Cache-Control': 'no-cache'}), timeout=3) as response:
                raw = response.read()
            nodes = list(walk(json.loads(raw)['current-projects']))
            colored = [n for n in nodes if n.get('payload', {}).get('taskColor')]
            target = [n for n in nodes if n['content'].startswith(f'[TASK:{TASK}] succeeded;')]
            if status == ('succeeded',) and len(target) == 1:
                if len(colored) == 1 and colored[0] is target[0] and target[0]['payload']['taskColor'] == 'review':
                    print(json.dumps({'task': TASK, 'broker_status': status[0], 'color': 'review',
                        'colored_count': 1, 'http_sha256': hashlib.sha256(raw).hexdigest(),
                        'browser_verified': False}))
                    return 0
                if colored and not colored[0]['content'].startswith(f'[TASK:{TASK}] '):
                    raise SystemExit('Different task selected; inspect newer receipt, no automatic retry.')
            time.sleep(1)
    raise SystemExit('No matching terminal publication within 45s; inspect broker/outbox. No mutation performed.')

if __name__ == '__main__':
    sys.exit(main())
