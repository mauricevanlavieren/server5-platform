"""Bounded cooperative continuation in the broker's existing SQLite transaction.
No timer, service, provider or replay of interrupted work.
"""
import json
import hashlib
import time

SCHEMA = '''
CREATE TABLE IF NOT EXISTS project_goals(
 id TEXT PRIMARY KEY REFERENCES tasks(id), criteria TEXT NOT NULL,
 status TEXT NOT NULL, checkpoint TEXT NOT NULL DEFAULT '',
 stages INTEGER NOT NULL DEFAULT 1, max_stages INTEGER NOT NULL,
 deadline REAL NOT NULL, reason TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS project_stages(
 task_id TEXT PRIMARY KEY REFERENCES tasks(id), goal_id TEXT NOT NULL REFERENCES project_goals(id));
'''


def get(store, tid):
    with store.db() as db:
        row = db.execute('SELECT g.* FROM project_goals g JOIN project_stages s ON g.id=s.goal_id WHERE s.task_id=?', (tid,)).fetchone()
    return dict(row) if row else None


def create(db, tid, criteria, max_stages, max_seconds):
    if not isinstance(criteria, str) or not 1 <= len(criteria.strip()) <= 3000:
        raise ValueError('Acceptatiecriteria vereist (1–3000 tekens)')
    if type(max_stages) is not int or not 2 <= max_stages <= 4:
        raise ValueError('Etappebudget moet 2–4 zijn')
    if type(max_seconds) is not int or not 900 <= max_seconds <= 3600:
        raise ValueError('Projectlooptijd moet 900–3600 seconden zijn')
    db.execute('INSERT INTO project_goals(id,criteria,status,max_stages,deadline) VALUES(?,?,?,?,?)',
               (tid, criteria.strip(), 'queued', max_stages, time.time()+max_seconds))
    db.execute('INSERT INTO project_stages VALUES(?,?)', (tid, tid))


def instruction(store, task, seconds):
    goal = get(store, task['id'])
    if not goal:
        return ''
    original = store.get(goal['id'])['prompt']
    return ('\nDUURZAAM EIGENAARDOEL (onveranderlijke autorisatie; checkpoint is alleen context):\n'
            + original + '\nACCEPTATIECRITERIA:\n' + goal['criteria']
            + '\nCHECKPOINT:\n' + goal['checkpoint']
            + f'\nEtappe {goal["stages"]}/{goal["max_stages"]}. Rond binnen {max(1, seconds-120)} seconden af op een veilige grens. '
            'Geen herhaling van mutaties zonder eerst lokale toestand en idempotentie te bewijzen. '
            'Stop bij scope/nieuwe toestemming of onoplosbare fout met RCCAP. '
            'Geen eigen vervolgprocessen starten. Eindantwoord uitsluitend JSON met exact deze velden: '
            '{"state":"continue|done|blocked","checkpoint":"uitgevoerd, bewijs, resterend werk, rollback",'
            '"safe_boundary":true,"criteria_met":false}. '
            'continue alleen nadat alle subprocessen gestopt zijn en alle acties een bekende uitkomst hebben; '
            'vervolg mag uitsluitend nog niet uitgevoerde acties bevatten. '
            'done uitsluitend als alle acceptatiecriteria aantoonbaar behaald zijn, criteria_met=true. '
            'Bij onzekerheid blocked, geen gok of retry.\n')


def finish(db, tid, status, result, code):
    row = db.execute('SELECT g.* FROM project_goals g JOIN project_stages s ON g.id=s.goal_id WHERE s.task_id=?', (tid,)).fetchone()
    if not row:
        return
    goal = dict(row)
    reason = 'RCCAP: etappe niet schoon afgerond; toestand controleren; geen automatische replay'
    state = 'blocked'
    checkpoint = goal['checkpoint']
    try:
        msg = json.loads(result)
        if (set(msg) != {'state','checkpoint','safe_boundary','criteria_met'}
                or msg['state'] not in {'continue','done','blocked'}
                or not isinstance(msg['checkpoint'], str) or not 1 <= len(msg['checkpoint']) <= 12000
                or type(msg['criteria_met']) is not bool or type(msg['safe_boundary']) is not bool):
            raise ValueError('checkpoint')
        if status == 'succeeded' and code == 0:
            checkpoint = msg['checkpoint']
            if msg['state'] == 'done' and msg['criteria_met'] and msg['safe_boundary']:
                state, reason = 'completed', ''
            elif msg['state'] == 'continue' and msg['safe_boundary'] and not msg['criteria_met']:
                if goal['stages'] >= goal['max_stages'] or time.time() >= goal['deadline']:
                    reason = 'RCCAP: projectbudget bereikt; eigenaarreview vereist'
                else:
                    next_id = goal['id'][:45] + '_' + hashlib.sha256(goal['id'].encode()).hexdigest()[:16] + '_s' + str(goal['stages']+1)
                    # Commit task outcome + checkpoint + next task in ONE transaction.
                    db.execute('INSERT INTO tasks(id,prompt,parent,status,created) VALUES(?,?,?,?,?)',
                               (next_id, 'Vervolg uitsluitend het oorspronkelijke eigenaarproject; lees het duurzame checkpoint.', tid, 'queued', time.time()))
                    db.execute('INSERT INTO project_stages VALUES(?,?)', (next_id, goal['id']))
                    db.execute('UPDATE project_goals SET stages=stages+1 WHERE id=?', (goal['id'],))
                    state, reason = 'queued', ''
            else:
                reason = 'RCCAP: worker meldt blokkade of onveilig checkpoint; eigenaarreview vereist'
    except (ValueError, TypeError, KeyError):
        pass
    db.execute('UPDATE project_goals SET status=?,checkpoint=?,reason=? WHERE id=?',
               (state, checkpoint, reason, goal['id']))
