"""Explicit owner submissions; metadata stays exclusively in Test Projects."""
import json
import hashlib
import fcntl
from pathlib import Path
from datetime import datetime, timezone
from mindmap_lifecycle import atomic

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'mindmap/public/test-projects.json'
HISTORY = ROOT / 'docs/test-projects/queue'
SCHEMA = '''CREATE TABLE IF NOT EXISTS test_project_tasks(task_id TEXT PRIMARY KEY);'''

def linked(db, tid):
    return db.execute('SELECT 1 FROM test_project_tasks WHERE task_id=?', (tid,)).fetchone() is not None

def instruction(tid):
    return f'''\nTEST PROJECTS-contract: taak {tid}; Current Projects nooit wijzigen.
De broker maakt een aparte levende testkaart. Gebruik scripts/test-projects.py voor echte
voortgang: add --id UNIEK --parent ID --title TITEL; complete --id ID --proof BEWIJS.
Lees mindmap/public/test-projects.json voor de huidige IDs. Voeg alleen stappen toe
wanneer die werkelijk nodig zijn; werk van diepste blad terug. Elke afgeronde stap
wordt gesnoeid. Voltooi uiteindelijk wortel {tid} met bewijs van gecontroleerd resultaat.
Bij blokkade: block --id ACTIEF_ID --cause OORZAAK --solution OPLOSSING
--next-action VERVOLG. Geen simulatie, automatische retry of brokerherstart.
'''

def publish(event):
    HISTORY.mkdir(exist_ok=True)
    with (ROOT / 'docs/test-projects/writer.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        tid = event['task_id']
        record = HISTORY / (tid + '.json')
        s = json.loads(record.read_text()) if record.exists() else None
        if s and s.get('broker_seq', -1) >= event['seq']:
            return
        if not s:
            if PUBLIC.exists():
                prior = PUBLIC.read_bytes()
                atomic(HISTORY/('prior-'+hashlib.sha256(prior).hexdigest()+'.json'),prior)
            # New tasks cannot replace an unfinished card; submit checks queue atomically.
            s = {'test':True, 'task_id':tid, 'label':'TEST — echte Codex-opdracht',
                 'used_ids':[tid], 'root':{'id':tid,'title':'Codex-opdracht','status':'active','children':[]}}
        if PUBLIC.exists():
            current = json.loads(PUBLIC.read_text())
            if current.get('task_id') == tid:
                s = current
        status = event['status']
        if status == 'running' and s['root']['status'] != 'done':
            s['root']['title'] = 'Codex voert eigenaaropdracht uit'
        if status in {'failed','cancelled','interrupted'} or (status == 'succeeded' and s['root']['status'] != 'done'):
            def walk(n):
                yield n
                for c in n['children']: yield from walk(c)
            nodes = list(walk(s['root']))
            active = next((n for n in nodes if n['status']=='active'), nodes[-1])
            for n in nodes:
                if n['status']=='active': n['status']='pending'
            active['status']='blocked'
            active['block']={'cause':f'RCCAP: broker {status}; voltooiingsbewijs controleren',
                             'solution':'Controleer resultaat en bestanden; geen automatische replay',
                             'next_action':'Eigenaar bepaalt expliciet herstel of vervolg'}
        s.update(broker_status=status, broker_seq=event['seq'], updated_at=datetime.now(timezone.utc).isoformat())
        data = json.dumps(s,ensure_ascii=False,indent=2)
        atomic(PUBLIC,data)
        atomic(record,data)
