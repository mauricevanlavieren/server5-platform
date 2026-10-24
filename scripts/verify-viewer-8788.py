#!/usr/bin/env python3
"""Read-only foreground verification; no task submission or background polling."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
BASE = 'http://192.168.1.245:8788/'

def walk(node):
    yield node
    for child in node.get('children', []):
        yield from walk(child)

def get(name):
    with urllib.request.urlopen(urllib.request.Request(BASE + name, headers={'Cache-Control':'no-cache'}), timeout=3) as response:
        return response.read()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', required=True)
    parser.add_argument('--expect', choices=['running','succeeded','failed','accepted'], default='succeeded')
    parser.add_argument('--timeout', type=int, default=45)
    args = parser.parse_args()
    expected_status = 'succeeded' if args.expect == 'accepted' else args.expect
    expected_color = {'running':'running','succeeded':'review','failed':'failed','accepted':'accepted'}[args.expect]
    deadline = time.monotonic() + min(max(args.timeout, 1), 60)
    dbpath = Path.home()/'.local/state/server5-commandcenter/mvp/tasks.sqlite3'
    with sqlite3.connect(dbpath.as_uri()+'?mode=ro', uri=True) as db:
        while True:
            status = db.execute('SELECT status FROM tasks WHERE id=?',(args.task,)).fetchone()
            raw = get('map.json')
            nodes = list(walk(json.loads(raw)['current-projects']))
            colored = [n for n in nodes if n.get('payload',{}).get('taskColor')]
            matching = len(colored) == 1 and colored[0]['content'].startswith(f'[TASK:{args.task}] {expected_status};') and colored[0]['payload']['taskColor'] == expected_color
            if status == (expected_status,) and matching:
                for name in ['index.html', 'viewer.js', 'map.json']:
                    if get(name) != (ROOT/'mindmap/public'/name).read_bytes():
                        raise SystemExit(f'HTTP/disk mismatch: {name}; retry after publisher settles')
                html = get('index.html').decode()
                assert '.current-step{background:#eef0f2;' in html
                assert './viewer.js?v=20261023-neutral-project-step-1' in html
                print(json.dumps({'task':args.task,'broker_status':status[0], 'color':expected_color,
                    'colored_count':1,'historical_tasks_neutral':True,'http_disk_equal':True,
                    'current_step_background':'#eef0f2','map_sha256':hashlib.sha256(raw).hexdigest(),
                    'browser_verified':False}, indent=2))
                return
            if time.monotonic() >= deadline:
                raise SystemExit('Expected publication not observed; no mutation performed. A newer task may have superseded this task.')
            time.sleep(1)

if __name__ == '__main__':
    main()
