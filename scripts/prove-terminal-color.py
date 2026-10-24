#!/usr/bin/env python3
"""Real Codex + isolated broker/outbox + production map + live HTTP polling.
Threads exist only within this foreground acceptance run and are joined.
"""
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import urllib.request
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'web'))
import commandcenter as broker

DEST = ROOT/'docs/mindmaps/terminal-color-fix-20261023'
TID = 'TERMINAL-COLOR-E2E-20261023-001'
def nodes(n):
    yield n
    for child in n.get('children', []):
        yield from nodes(child)
def main():
    if (DEST/'proof.json').exists():
        raise SystemExit('Proof exists; no automatic worker retry')
    observations = []
    def observe(expected, timeout=12):
        deadline = time.monotonic()+timeout
        while time.monotonic()<deadline:
            with urllib.request.urlopen('http://192.168.1.245:8788/map.json', timeout=3) as r:
                raw=r.read()
            tree=json.loads(raw)['current-projects']
            all_nodes=list(nodes(tree))
            task=next((n for n in all_nodes if n['content'].startswith(f'[TASK:{TID}] {expected};')),None)
            if task:
                colored=[n for n in all_nodes if n.get('payload',{}).get('taskColor')]
                want={'queued':None,'running':'running','succeeded':'review'}[expected]
                assert task.get('payload',{}).get('taskColor')==want
                assert len(colored)==(0 if want is None else 1)
                (DEST/f'{expected}.json').write_bytes(raw)
                observations.append({'status':expected,'color':want,'colored_count':len(colored),'observed_at':time.time()})
                return
            time.sleep(1)
        raise AssertionError('HTTP phase not observed: '+expected)
    with tempfile.TemporaryDirectory(prefix='terminal-color-',dir=ROOT/'.task-backups') as directory:
        store=broker.Store(directory)
        store.mindmap_namespace='terminal-color-e2e-20261023'
        stop=threading.Event()
        dispatcher=threading.Thread(target=store.mindmap_loop,args=(stop,))
        dispatcher.start()
        try:
            store.submit('Read-only kleine acceptatieproef. Gebruik geen tools, wijzig niets, start geen subagent. Antwoord uitsluitend SERVER5_TERMINAL_COLOR_OK.',TID)
            observe('queued')
            task=store.claim()
            observe('running')
            broker.Worker(store,stop,timeout=120).run_task(task)
            terminal=time.time()
            result=store.get(TID)
            assert result['status']=='succeeded' and result['exit_code']==0
            assert 'SERVER5_TERMINAL_COLOR_OK' in result['result']
            observe('succeeded')
            elapsed=time.time()-terminal
            assert elapsed<5, elapsed
            proof={'task_id':TID,'real_codex':True,'isolated_task_db':True,'production_map_http':True,'terminal_to_http_seconds':elapsed,'observations':observations,'browser_used':False}
            (DEST/'proof.json').write_text(json.dumps(proof,indent=2)+'\n')
            print(json.dumps(proof,indent=2))
        finally:
            stop.set()
            dispatcher.join(timeout=50)
            assert not dispatcher.is_alive()
if __name__=='__main__': main()
