"""Explicit Current Projects routing; generic broker events never create cards."""
import json
import fcntl
from datetime import datetime, timezone
from mindmap_lifecycle import ROOT, atomic
PUBLIC = ROOT / 'mindmap/public/current-projects.json'
EVIDENCE = ROOT / 'docs/mindmaps/current-projects'

def has_active(state):
    def walk(n):
        yield n
        for c in n['children']: yield from walk(c)
    return any(n['status']=='active' for n in walk(state['root']))


def attach(state, tid):
    # Preserve historical projects and human review; never replace the live card.
    import copy
    state=copy.deepcopy(state)
    if has_active(state) or tid in state['used_ids']:
        raise ValueError('Actieve opdracht of reeds gebruikt project-ID')
    if state['root']['id'] != 'CURRENT-PROJECTS':
        state['root']={'id':'CURRENT-PROJECTS','title':'Current Projects','status':'pending','children':[state['root']]}
        if 'CURRENT-PROJECTS' not in state['used_ids']: state['used_ids'].append('CURRENT-PROJECTS')
    state['root']['status']='pending'
    state['root']['children'].append({'id':tid,'title':'Eigenaaropdracht — complete planning publiceren','status':'active','children':[]})
    state['used_ids'].append(tid)
    state['task_id']=tid
    state['project_id']=tid
    return state

def instruction(tid):
    return f"""\nCURRENT PROJECTS-contract: taak {tid}. TEST PROJECTS nooit wijzigen.
Maak EERST de complete concrete organische werkplanning onder opdrachtwortel {tid}.
Gebruik scripts/current-projects.py add --id UNIEK --parent ID --title TITEL.
Lees mindmap/public/current-projects.json voor stabiele IDs; behoud andere projecten en rode contractreviews.
Publiceer alle bekende uitvoerbare stappen en verifieer de publicatie vóór codewijzigingen.
Voer daarna ZELF achtereenvolgens alle onafhankelijke uitvoerbare stappen binnen de eigenaarsscope uit,
zonder nieuwe gebruikersprompt of goedkeuringsvraag voor gewone vervolgstappen.
Precies één actief diepste uitvoerbaar blad geel: activate --id ID.
Na echte voltooiing meteen complete --id ID --proof BEWIJS (snoeien); voer het volgende blad zelf uit.
Voeg alleen noodzakelijke nieuwe substappen toe. Een rode menselijke contractreview is geen toestemming:
laat die rood; werk andere onafhankelijke stappen af. Geen herhaling van geslaagde acties of eindeloze retries.
Bij een uitvoerbare fout: stop de opdracht niet en vraag geen nieuwe eigenaarprompt.
Onderzoek eerst de foutuitvoer en lokale oorzaak zonder secrets te lezen. Gebruik daarna
scripts/current-projects.py recover --id MISLUKT_ACTIEF_BLAD --cause CONCRETE_FOUT.
Dit publiceert diagnose, minimale correctie en hertest als organische subnodes, met stabiele IDs,
en bewaart maximaal TWEE herstelpogingen voor deze taak (ook bij wisselen van foutstap).
Lees de gepubliceerde IDs; voltooi diagnose met bewijs, corrigeer uitsluitend binnen de oorspronkelijke
opdracht, voltooi correctie met bewijs en herhaal uitsluitend de mislukte afgebakende stap.
Bij geslaagde hertest: complete hertest en oorspronkelijke stap; werk zelf het volgende blad af.
Bij mislukte hertest: rond uitsluitend het uitgevoerde onderzoek af met feitelijk foutbewijs,
activeer de oorspronkelijke foutstap en gebruik de resterende poging; claim nooit succes van de stap.
Bij budgetuitputting of onveilige/onoplosbare oorzaak: block het actieve blad met RCCAP oorzaak,
oplossing en concrete volgende actie. Geen nieuwe taak, proces, scheduler of deadlineverlenging.
Noodzakelijke eigenaarbeslissingen en scopegrenzen blijven gelden; timeout is nooit toestemming.
Stop alleen bij bewezen afronding (opdrachtwortel één groen blad), noodzakelijke eigenaarbeslissing,
werkelijke technische blokkade of harde workerdeadline. Geen automatische replay of eigen vervolgproces.
Bij echte blokkade: block --id ID --cause OORZAAK --solution OPLOSSING --next-action VERVOLG.
Voltooi uitsluitend de eigen opdrachtwortel na één korte functionele controle; behoud andere projecten.
Als brokeractivatie nodig is: niet zelf herstarten, pending activation plus exact onafhankelijk commando.

"""

def publish(event, namespace='broker', goal=None):
    EVIDENCE.mkdir(exist_ok=True)
    with (EVIDENCE/'writer.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        s=json.loads(PUBLIC.read_text())
        if s.get('task_id') != event['task_id']: return
        if event['seq'] <= s.get('broker_seq',-1): return
        def walk(n):
            yield n
            for c in n['children']: yield from walk(c)
        project=next((n for n in walk(s['root']) if n['id']==s.get('project_id',event['task_id'])),None)
        if project is not None and event['status'] in {'failed','cancelled','interrupted','blocked','succeeded'} and project['status']!='done':
            active=next((n for n in walk(project) if n['status']=='active'),None)
            if active is not None:
                active['status']='blocked'
                active['block']={'cause':'Broker '+event['status']+'; voltooiingsbewijs controleren','solution':'Controleer resultaat; geen automatische replay','next_action':'Herstel oorzaak of verkrijg noodzakelijke eigenaarbeslissing; behoud geslaagde stappen'}
        s.update(broker_seq=event['seq'],broker_status=event['status'],updated_at=datetime.now(timezone.utc).isoformat())
        atomic(PUBLIC,json.dumps(s,ensure_ascii=False,indent=2))
