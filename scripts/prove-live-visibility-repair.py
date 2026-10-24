#!/usr/bin/env python3
"""Explicit local acceptance: real broker transactions/publication/HTTP.

Uses the same QueueSubmitter as start_task, an isolated DB, and a fixed
read-only Python worker process (not a new Codex invocation). No service restart.
"""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import threading
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'web'))
import commandcenter as broker
import mindmap_lifecycle as lifecycle



def main():
    proof = ROOT / 'docs/mindmaps/live-visibility-repair-20261023'
    proof.mkdir(exist_ok=True)
    result_path = proof / 'result.json'
    if result_path.exists():
        raise SystemExit('Already recorded; do not silently repeat acceptance')
    tid = 'VISIBLE-REPAIR-E2E-20261023-001'
    phases = []
    before = lifecycle.SOURCE.read_text()

    def verify(status, color):
        assert store.drain_mindmap() == 1
        payload = urllib.request.urlopen('http://192.168.1.245:8788/map.json', timeout=5).read()
        assert payload == lifecycle.MAP.read_bytes()
        def walk(node):
            yield node
            for child in node.get('children', []):
                yield from walk(child)
        entries = list(walk(json.loads(payload)['current-projects']))
        task = [n for n in entries if n['content'].startswith(f'[TASK:{tid}] ')]
        assert len(task) == 1
        assert task[0]['content'].startswith(f'[TASK:{tid}] {status};')
        assert task[0]['payload'].get('taskColor') == color
        assert store.get(tid)['status'] == status
        (proof / (status + '.json')).write_bytes(payload)
        phases.append(dict(status=status, color=color, http_sha256=hashlib.sha256(payload).hexdigest()))

    with tempfile.TemporaryDirectory(prefix='task-visibility-', dir=ROOT / '.task-backups') as directory:
        store = broker.Store(directory)
        store.mindmap_namespace = 'live-visibility-repair-20261023'
        store.submit('Read-only fixed acceptance process; no owner project binding.', tid)
        store.submit('Read-only fixed acceptance process; no owner project binding.', tid)
        verify('queued', None)
        task = store.claim()
        assert task['id'] == tid
        verify('running', 'running')
        command = [sys.executable, '-c', 'import sys,json; sys.stdin.read(); print(json.dumps({"type":"item.completed","item":{"type":"agent_message","text":"TASK_VISIBILITY_OK"}}))']
        broker.Worker(store, threading.Event(), command=command, timeout=10).run_task(task)
        assert store.get(tid)['result'] == 'TASK_VISIBILITY_OK'
        verify('succeeded', 'review')
        with store.db() as db:
            outbox = [dict(r) for r in db.execute('SELECT * FROM mindmap_outbox ORDER BY seq')]
        assert len(outbox) == 3 and all(r['delivered'] for r in outbox)
    after = lifecycle.SOURCE.read_text()
    delta = dict(nodes_before=len(lifecycle.nodes(before)), nodes_after=len(lifecycle.nodes(after)),
                 removed=[s for s in before.splitlines() if s and s not in after.splitlines()],
                 added=[s for s in after.splitlines() if s and s not in before.splitlines()])
    assert not delta['removed'] and delta['nodes_after'] == delta['nodes_before'] + 1
    result = dict(scope='real Store.submit/claim/Worker with fixed read-only Python subprocess; isolated DB; production source/build/HTTP',
                  new_codex_invocation=False, active_broker_database_modified=False,
                  phases=phases, outbox=outbox, node_delta=delta,
                  receipts=[f'live-visibility-repair-20261023-{i:08d}.json' for i in (1, 2, 3)])
    lifecycle.atomic(result_path, json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
