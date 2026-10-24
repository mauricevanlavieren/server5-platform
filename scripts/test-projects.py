#!/usr/bin/env python3
"""Owner-authorized Test Projects only. Explicit worker updates; no simulator."""
import argparse
import copy
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'web'))
from mindmap_lifecycle import atomic
ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / 'mindmap/public/test-projects.json'
EVIDENCE = ROOT / 'docs/test-projects'

def walk(n):
    yield n
    for c in n['children']:
        yield from walk(c)

def update(s, action, node_id=None, parent_id=None, title=None, cause=None, solution=None, next_action=None, proof=None, independent=False):
    s = copy.deepcopy(s)
    nodes = {n['id']:n for n in walk(s['root'])}
    n = nodes.get(node_id)
    if action == 'recover':
        project = nodes.get(s.get('project_id'))
        if (not independent or not project or not n or n['children'] or
                n['status'] != 'active' or n not in list(walk(project)) or not cause):
            raise ValueError('Herstel vereist actief eigen Current Projects-blad en concrete foutoorzaak')
        attempts = s.setdefault('recovery_attempts', {})
        task_attempts = attempts.setdefault(s['task_id'], [])
        if len(task_attempts) >= 2:
            raise ValueError('Herstelbudget verbruikt (2); publiceer RCCAP met concrete volgende actie')
        attempt = len(task_attempts) + 1
        ids = [f'{s["task_id"]}-recovery-{attempt}-{step}' for step in ('diagnose','fix','retry')]
        if any(i in s['used_ids'] for i in ids):
            raise ValueError('Herstel-ID reeds gebruikt; geen replay')
        task_attempts.append({'node_id':node_id, 'cause':cause, 'ids':ids})
        n['status'] = 'pending'
        n['children'] = [dict(id=i, title=t, status='active' if index == 0 else 'pending', children=[])
                         for index, (i,t) in enumerate(zip(ids, (
                             'Fout onderzoeken: ' + cause,
                             'Minimale correctie binnen oorspronkelijke scope',
                             'Alleen mislukte stap opnieuw testen en vervolg controleren')))]
        s['used_ids'].extend(ids)
    elif action == 'add':
        if node_id in s['used_ids'] or parent_id not in nodes or not title:
            raise ValueError('Uniek stabiel ID, bestaande ouder en titel vereist')
        if independent and nodes[parent_id]['status'] in {'done','blocked'}:
            raise ValueError('Afgeronde of geblokkeerde ouder niet uitbreiden')
        if s['root']['status'] == 'done':
            raise ValueError('Afgeronde test eerst expliciet opnieuw initialiseren')
        if not independent and any(x['status'] == 'blocked' for x in nodes.values()):
            raise ValueError('Los blokkade expliciet op')
        for x in nodes.values():
            if x['status'] == 'active': x['status'] = 'pending'
        nodes[parent_id]['children'].append({'id':node_id,'title':title,'status':'active','children':[]})
        s['used_ids'].append(node_id)
    elif action == 'activate':
        if not n or n['children'] or n['status'] == 'done': raise ValueError('Alleen open blad activeren')
        if n['status'] == 'blocked' and not proof: raise ValueError('Bewijs van oplossing vereist')
        for x in nodes.values():
            if x['status'] == 'active': x['status'] = 'pending'
        n['status']='active'
        n.pop('block',None)
    elif action == 'block':
        if not n or n['status'] != 'active' or not all([cause,solution,next_action]):
            raise ValueError('Actieve stap plus oorzaak, oplossing en volgende actie vereist')
        n['status']='blocked'
        n['block']={'cause':cause,'solution':solution,'next_action':next_action}
    elif action == 'complete':
        if not n or n['children'] or n['status'] != 'active' or not proof:
            raise ValueError('Alleen actief blad met bewijs afronden; rood blijft behouden')
        if n is s['root'] or (independent and n['id']==s.get('project_id')):
            n['status']='done'
        else:
            parent=next(x for x in nodes.values() if n in x['children'])
            parent['children'].remove(n)
            leaves=[x for x in walk(s['root']) if not x['children']]
            if independent:
                leaves=[x for x in leaves if x['status'] not in {'blocked','done'}]
            if leaves:
                deepest=max(leaves,key=lambda x:depth(s['root'],x['id']))
                deepest['status']='active'
    else: raise ValueError('Onbekende actie')
    live=list(walk(s['root']))
    active=[n for n in live if n['status']=='active']
    blocked=[n for n in live if n['status']=='blocked']
    if s['root']['status']=='done':
        assert len(live)==1 and not active and not blocked
    elif blocked and not independent:
        assert not active
    elif independent:
        eligible=[x for x in live if not x['children'] and x['status'] not in {'blocked','done'}]
        assert len(active) <= 1
        if active:
            assert not active[0]['children']
            assert depth(s['root'],active[0]['id']) == max(depth(s['root'],x['id']) for x in eligible)
    else:
        assert len(active)==1 and not active[0]['children']
        assert max(depth(s['root'],x['id']) for x in live)==depth(s['root'],active[0]['id'])
    s['updated_at']=datetime.now(timezone.utc).isoformat()
    return s

def depth(n, target, d=0):
    if n['id']==target: return d
    return max([depth(c,target,d+1) for c in n['children']]+[-1])

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['init','add','recover','activate','block','complete','snapshot'])
    for arg in ['id','parent','title','cause','solution','next-action','proof','evidence']:
        p.add_argument('--'+arg)
    a=p.parse_args()
    EVIDENCE.mkdir(exist_ok=True)
    with (EVIDENCE/'writer.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if a.action=='init':
            if STATE.exists(): p.error('Bestaande toestand behouden; init geweigerd')
            s={'test':True,'label':'TEST — fictieve opdracht; geen dashboard gebouwd','used_ids':['dashboard'],'root':{'id':'dashboard','title':'Dashboard bouwen','status':'active','children':[]},'updated_at':datetime.now(timezone.utc).isoformat()}
        else:
            s=json.loads(STATE.read_text())
            if s.get('task_id') and os.environ.get('SERVER5_TASK_ID') != s['task_id']:
                p.error('Alleen de gekoppelde worker mag deze kaart wijzigen')
            if a.action!='snapshot':
                s=update(s,a.action,a.id,a.parent,a.title,a.cause,a.solution,a.next_action,a.proof)
        atomic(STATE,json.dumps(s,ensure_ascii=False,indent=2))
        if s.get('task_id'):
            history=EVIDENCE/'queue'
            history.mkdir(exist_ok=True)
            stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
            atomic(history/(s['task_id']+'-step-'+stamp+'.json'),json.dumps({'action':a.action,'proof':a.proof,'state':s},ensure_ascii=False,indent=2))
        if a.evidence:
            if not a.evidence.replace('-','').isalnum(): p.error('Ongeldige bewijsnaam')
            atomic(EVIDENCE/(a.evidence+'.json'),json.dumps({'action':a.action,'proof':a.proof,'state':s},ensure_ascii=False,indent=2))
        print(json.dumps({'nodes':len(list(walk(s['root']))),'active':[n['id'] for n in walk(s['root']) if n['status']=='active'],'root':s['root']['status']}))
if __name__=='__main__': main()
