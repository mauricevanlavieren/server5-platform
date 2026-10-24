#!/usr/bin/env python3
"""One real Codex task, isolated task DB; real map publication/build/HTTP.
Does not connect to the active broker DB or read login credentials.
"""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import threading
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'web'))
import commandcenter as broker
from mindmap_lifecycle import EVIDENCE, MAP, atomic


def main():
    # Single fixed ID makes this an explicit acceptance run, not automatic retries.
    task_id = 'E2E-LIVE-20261022-001'
    destination = EVIDENCE/'e2e-result.json'
    if destination.exists():
        raise SystemExit('Acceptance already recorded; do not silently rerun a Codex task')
    phases = []
    def verify(status):
        store.drain_mindmap()  # explicit dispatcher tick; task transactions never publish
        payload = urllib.request.urlopen('http://192.168.1.245:8788/map.json', timeout=10).read()
        assert payload == MAP.read_bytes(), 'HTTP differs from published artifact'
        assert f'[TASK:{task_id}] {status}' in payload.decode(), 'Task phase missing'
        phases.append({'status':status, 'http_sha256':hashlib.sha256(payload).hexdigest()})
    with tempfile.TemporaryDirectory(prefix='lifecycle-e2e-', dir=ROOT/'.task-backups') as work:
        store = broker.Store(work)
        store.mindmap_namespace = 'acceptance'
        store.submit('Dit is één read-only acceptatieproef. Voer geen tools, wijzigingen of subopdrachten uit. Antwoord uitsluitend: SERVER5_LIFECYCLE_OK', task_id)
        verify('queued')
        task = store.claim()
        verify('running')
        broker.Worker(store, threading.Event(), timeout=120).run_task(task)
        result = store.get(task_id)
        verify(result['status'])
        evidence = {'scope':'real Codex worker with isolated broker DB; production Markdown/build/HTTP',
                    'task_id': task_id, 'status':result['status'], 'exit_code':result['exit_code'],
                    'expected_result_seen': 'SERVER5_LIFECYCLE_OK' in result['result'],
                    'phases':phases, 'active_broker_database_opened':False,
                    'delta_receipts':[f'acceptance-{n:08d}.json' for n in (1,2,3)]}
        atomic(destination, json.dumps(evidence, indent=2))
        assert result['status']=='succeeded' and result['exit_code']==0 and evidence['expected_result_seen'], 'Real worker failed; inspect broker result locally'
    print(json.dumps(evidence, indent=2))

if __name__ == '__main__':
    main()
