#!/usr/bin/env python3
"""One bounded real Codex acceptance; isolated state, no service or poller."""
import json
from pathlib import Path
import sys
import threading
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'web'))
from commandcenter import Store, Worker, ROOT

base = ROOT/'docs/autonomy/acceptance'
base.mkdir(parents=True,exist_ok=True)
state = ROOT/'.task-backups/autonomy-acceptance-20261023'
if (base/'receipt.json').exists() or state.exists():
    raise SystemExit('One-shot test already exists; preserve evidence, no replay')
s = Store(state)
tid = 'autonomy_acceptance_20261023_001'
prompt = '''Dit is het expliciet geautoriseerde onschadelijke testproject voor brokercontinuatie.
Scope uitsluitend twee NIEUWE tekstbestanden in docs/autonomy/acceptance. Geen andere wijzigingen,
geen services, geen tools installeren, geen agents, geen secrets, geen externe systemen.
Deze acceptatie vereist bewust EXACT TWEE etappes. Etappe 1: maak met exclusive create (mode x)
part1.txt met exact 'stage-one\\n'. Controleer inhoud. Geef daarna direct het vereiste JSON-checkpoint
met state=continue, safe_boundary=true, criteria_met=false. Maak final.txt NIET in etappe 1.
Etappe 2 (als checkpoint meldt dat part1 bestaat): lees/valideer part1.txt, schrijf met exclusive create
final.txt met exact 'stage-one\\nstage-two\\n'; controleer inhoud van beide en meld JSON state=done,
safe_boundary=true, criteria_met=true. Herhaal nooit de creatie van part1. Bij afwijkingen blocked.
Rollback: alleen deze eigen testbestanden mogen later door eigenaar worden opgeruimd; nu bewaren.
Lees lokale AGENTS-afspraken maar wijzig geen andere bestanden of mindmap; broker regelt metadata.'''
s.submit(prompt, tid, goal=dict(criteria='part1.txt == stage-one newline; final.txt == stage-one newline stage-two newline; twee aparte succesvolle Codex-etappes',max_stages=2,max_seconds=900))
trace=[]
for stage in (1,2):
    task=s.claim()
    if task is None:break
    started=time.time()
    Worker(s,threading.Event(),timeout=180).run_task(task)
    finished=s.get(task['id'])
    trace.append(dict(id=task['id'],status=finished['status'],exit_code=finished['exit_code'],seconds=round(time.time()-started,2),goal=finished['goal'],result=finished['result']))
    if stage==1:
        # Reopen and invoke the same recovery used by service startup. A queued
        # successor survives; running mutation is never replayed.
        s=Store(state);s.recover()
        trace[-1]['reopened_goal_status']=s.get(tid)['goal']['status']
    print(json.dumps({'stage':stage,'task_id':task['id'],'status':finished['status'],'project':finished['goal']['status']}),flush=True)
passed=(len(trace)==2 and all(t['status']=='succeeded' for t in trace)
        and s.get(tid)['goal']['status']=='completed'
        and (base/'part1.txt').read_text()=='stage-one\n'
        and (base/'final.txt').read_text()=='stage-one\nstage-two\n')
receipt=dict(passed=passed,real_codex=True,live_service=False,trace=trace)
(base/'receipt.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('ACCEPTANCE '+('PASS' if passed else 'FAIL'),flush=True)
raise SystemExit(0 if passed else 1)
