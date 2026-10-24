"""Broker-owned metadata publication. Never opens a task database or reads worker text."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs/mindmaps/import-current-projects.md'
EVIDENCE = ROOT / 'docs/mindmaps/live-lifecycle'
MAP = ROOT / 'mindmap/public/map.json'
BINDINGS = ROOT / 'docs/mindmaps/task-project-bindings.json'
CLOSURES = ROOT / 'docs/mindmaps/project-closures.json'
SCHEMA = '''
CREATE TABLE IF NOT EXISTS mindmap_outbox(
 seq INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL,
 status TEXT NOT NULL, exit_code INTEGER, at TEXT NOT NULL,
 delivered INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS mindmap_retry(
 seq INTEGER PRIMARY KEY, attempts INTEGER NOT NULL DEFAULT 0,
 next_at REAL NOT NULL DEFAULT 0, error_type TEXT);
CREATE TRIGGER IF NOT EXISTS mindmap_insert AFTER INSERT ON tasks BEGIN
 INSERT INTO mindmap_outbox(task_id,status,exit_code,at)
 VALUES(NEW.id,NEW.status,NEW.exit_code,strftime('%Y-%m-%dT%H:%M:%fZ','now')); END;
CREATE TRIGGER IF NOT EXISTS mindmap_update AFTER UPDATE OF status ON tasks
 WHEN OLD.status != NEW.status BEGIN
 INSERT INTO mindmap_outbox(task_id,status,exit_code,at)
 VALUES(NEW.id,NEW.status,NEW.exit_code,strftime('%Y-%m-%dT%H:%M:%fZ','now')); END;
'''


def atomic(path, data):
    path = Path(path)
    if path.is_symlink():
        raise ValueError('Symlink target rejected')
    fd, name = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data if isinstance(data, bytes) else data.encode())
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def nodes(source):
    result, stack = {}, []
    for line in source.splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r'(#{1,6}) (.+)', line)
        if not match:
            raise ValueError('Only plain headings allowed')
        level = len(match[1])
        if level > len(stack) + 1:
            raise ValueError('Invalid hierarchy')
        stack = stack[:level]
        if len(stack) < level:
            stack.append(0)
        stack[-1] += 1
        if line in result:
            raise ValueError('Duplicate heading rejected')
        result[line] = '.'.join(map(str, stack))
    return result


def reconcile(source, rules=None):
    """Apply explicitly accepted scope, never infer project completion from success.

    Rules are local owner-authorized configuration, not worker output. Evidence
    and terminal receipts are hash-bound; exact preimages protect unrelated work.
    The normal build remains the final project/current-step invariant guard.
    """
    if rules is None:
        rules = json.loads(CLOSURES.read_text()) if CLOSURES.exists() else []
    lines = source.splitlines()
    for rule in rules:
        pid, sid = rule['project_id'], rule['step_id']
        targets = rule['changes']
        # Durable marker survives subsequent project status/position changes.
        marker = f'[ACCEPTED:{rule["id"]}]'
        if any(marker in line for line in lines):
            continue
        if not any(marker in change['after'] for change in targets):
            raise ValueError('Missing durable acceptance marker')
        for proof in rule['proofs']:
            path = (ROOT / proof['path']).resolve()
            if not path.is_relative_to((ROOT / 'docs/mindmaps').resolve()):
                raise ValueError('Evidence outside allowed directory')
            data = path.read_bytes()
            if hashlib.sha256(data).hexdigest() != proof['sha256']:
                raise ValueError('Acceptance evidence changed')
        if rule['receipt'] not in [p['path'] for p in rule['proofs']]:
            raise ValueError('Unbound terminal receipt')
        receipt = json.loads((ROOT / rule['receipt']).read_text())
        event = receipt['event']
        if event['task_id'] != rule['task_id'] or event['status'] != 'succeeded' or event['exit_code'] != 0:
            raise ValueError('No successful terminal receipt')
        projects = [i for i, line in enumerate(lines) if line.startswith('## ') and f'[PROJECT:{pid}]' in line]
        if len(projects) != 1:
            raise ValueError('Ambiguous project binding')
        start = projects[0]
        end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith('## ')), len(lines))
        if not any(f'[STEP:{sid}]' in line and ('🔄 HUIDIGE STAP' in line or ('BEOORDELING OPEN' in line and f'[LINK-TASK:{rule["task_id"]}]' in line)) for line in lines[start:end]):
            raise ValueError('Current step precondition changed')
        if rule['outcome'] not in {'step_finished', 'project_finished'}:
            raise ValueError('Unknown acceptance scope')
        if rule['outcome'] == 'project_finished':
            proof_path = rule.get('project_acceptance')
            if proof_path not in [p['path'] for p in rule['proofs']]:
                raise ValueError('Whole-project acceptance required')
            acceptance = json.loads((ROOT / proof_path).read_text())
            if acceptance.get('project_id') != pid or acceptance.get('outcome') != 'project_finished' or acceptance.get('accepted') is not True:
                raise ValueError('Whole-project scope not accepted')
        for change in targets:
            old, new = change['before'], change['after']
            if lines.count(old) != 1 or not re.fullmatch(r'#{2,4} [^\n]+', new):
                raise ValueError('Closure preimage conflict')
            if f'[{change["id"]}]' not in old or f'[{change["id"]}]' not in new:
                raise ValueError('Stable closure ID changed')
            if '[VOLTOOID]' in new and change['id'].startswith('PROJECT:') and rule['outcome'] != 'project_finished':
                raise ValueError('Step acceptance cannot finish project')
            lines[lines.index(old)] = new
    return '\n'.join(lines).rstrip() + '\n'


def link_project_step(source, event, bindings):
    """Owner-managed metadata only. Never inspect prompts/results or activate projects."""
    binding = bindings.get(event['task_id'])
    if binding is None:
        return source, 'fallback: geen expliciete project/step-koppeling'
    if not isinstance(binding, dict) or set(binding) != {'project_id', 'step_id', 'title'}:
        return source, 'fallback: ongeldige koppelmetadata'
    pid, sid, title = (binding[k] for k in ('project_id', 'step_id', 'title'))
    if (not all(isinstance(v, str) for v in (pid, sid, title))
            or not re.fullmatch(r'[A-Z0-9-]{1,80}', pid)
            or not re.fullmatch(r'[A-Z0-9-]{1,80}', sid)
            or not re.fullmatch(r'[\w ,.:()/—-]{1,160}', title)):
        return source, 'fallback: ongeldige koppelmetadata'
    lines = source.splitlines()
    projects = [i for i, line in enumerate(lines) if line.startswith('## ') and f'[PROJECT:{pid}]' in line]
    if len(projects) != 1:
        return source, 'fallback: project ontbreekt of is ambigu'
    start = projects[0]
    if f'[PROJECT:{pid}] [ACTIEF]' not in lines[start]:
        return source, 'fallback: project is niet ACTIEF; projectstatus behouden'
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith('## ')), len(lines))
    steps = [i for i in range(start + 1, end) if lines[i].startswith('### ') and f'[STEP:{sid}]' in lines[i]]
    if len(steps) != 1 or sum(f'[STEP:{sid}]' in line for line in lines) != 1:
        return source, 'fallback: step ontbreekt of is ambigu'
    target = steps[0]
    if any('🔄 HUIDIGE STAP' in lines[i] for i in range(start + 1, end) if i != target):
        return source, 'fallback: andere huidige stap behouden; RCCAP: expliciete positie-review nodig'
    if '[ACCEPTED:' in lines[target] or '✅ VOLTOOID' in lines[target]:
        return source, 'fallback: geaccepteerde stap behouden'
    # A different task cannot take over an in-flight step.
    owners = re.findall(r'\[LINK-TASK:([^]\n]+)\]', lines[target])
    if owners and owners != [event['task_id']]:
        return source, 'fallback: step is aan andere taak gekoppeld; RCCAP: positie-review nodig'
    status = event['status']
    label = {'queued': 'GEPLAND', 'running': '🔄 HUIDIGE STAP',
             'succeeded': 'BEOORDELING OPEN — worker gereed; inhoudelijke acceptatie vereist',
             'failed': 'RCCAP — uitvoering mislukt; resultaat controleren; handmatig vervolg',
             'blocked': 'RCCAP — uitvoering geblokkeerd; oorzaak controleren; handmatig vervolg',
             'cancelled': 'RCCAP — geannuleerd; handmatig vervolg',
             'interrupted': 'RCCAP — onderbroken; handmatig vervolg'}[status]
    lines[target] = f"### [STEP:{sid}] {label} — {title} [LINK-TASK:{event['task_id']}]"
    return '\n'.join(lines).rstrip() + '\n', f'gekoppeld: PROJECT:{pid}; STEP:{sid}; {status}'


def publish(event, namespace='broker', goal=None):
    from current_projects_bridge import publish as current_publish
    return current_publish(event, namespace, goal)

def publish_legacy(event, namespace='broker', goal=None):
    if set(event) != {'seq', 'task_id', 'status', 'exit_code', 'at'}:
        raise ValueError('Metadata fields rejected')
    tid, status, code = event['task_id'], event['status'], event['exit_code']
    if not re.fullmatch(r'[A-Za-z0-9_-]{16,80}', tid) or status not in {'queued','running','succeeded','failed','cancelled','interrupted','blocked'}:
        raise ValueError('Invalid metadata')
    if (code is not None and type(code) is not int) or (status in {'queued','running'} and code is not None) or (status == 'succeeded' and code != 0):
        raise ValueError('Contradictory status')
    if not re.fullmatch(r'[A-Za-z0-9_-]+', namespace) or type(event['seq']) is not int or event['seq'] < 1:
        raise ValueError('Invalid event identity')
    stamp = datetime.fromisoformat(event['at'].replace('Z', '+00:00'))
    if stamp.tzinfo is None:
        raise ValueError('Timestamp must include zone')
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    key = f'{namespace}-{event["seq"]:08d}'
    with (EVIDENCE / 'writer.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if (EVIDENCE / 'disabled').exists():
            raise ValueError('Publication disabled')
        receipt = EVIDENCE / (key + '.json')
        if receipt.exists():
            if json.loads(receipt.read_text())['event'] != event:
                raise ValueError('Event ID conflict')
            return
        before = SOURCE.read_text()
        paths_before = nodes(before)
        anchor = '### [AUTO-LIFECYCLE] Automatische brokerstatus — metadata, geen inhoudelijke resultaatacceptatie'
        lines = before.splitlines()
        if lines.count('## Workflow') != 1:
            raise ValueError('Workflow anchor ambiguous')
        if anchor not in lines:
            lines += ['', anchor]
        if lines.count(anchor) != 1 or lines.index(anchor) < lines.index('## Workflow'):
            raise ValueError('Managed anchor ambiguous')
        # Only exact task ID and its own temporary child are replaceable.
        prefix = f'#### [TASK:{tid}] '
        old = [i for i, line in enumerate(lines) if line.startswith(prefix)]
        if len(old) > 1:
            raise ValueError('Ambiguous task')
        children = []
        acceptance = []
        if old:
            start = old[0]
            # Explicit owner acceptance in the source survives idempotent
            # succeeded publications, including tasks in the neutral inbox.
            acceptance = re.findall(r'\[ACCEPTED:[A-Za-z0-9_-]+\]', lines[start])
            previous = lines[start][len(prefix):].split(';', 1)[0]
            transitions = {
                'queued': {'queued','running','failed','cancelled','interrupted','blocked'},
                'running': {'running','succeeded','failed','cancelled','interrupted','blocked'},
                'succeeded': {'succeeded'}, 'failed': {'failed'},
                'blocked': {'blocked'}, 'cancelled': {'cancelled'}, 'interrupted': {'interrupted'}}
            if status not in transitions.get(previous, set()):
                raise ValueError('Status regression rejected')
            end = start + 1
            while end < len(lines) and (not lines[end].strip() or lines[end].startswith('#####')):
                if lines[end].strip():
                    children.append(lines[end])
                end += 1
            allowed = f'##### [TEMP:{tid}] Technische uitvoering — bewaren zolang taak open is'
            if (children.count(allowed) > 1 or any(
                    child != allowed and not child.startswith(f'##### [RCCAP:{tid}] ')
                    for child in children)):
                raise ValueError('Unknown children; preserve open work')
            del lines[start:end]
        link_event = dict(event)
        # A goal is binding context only: its present aggregate state must never
        # rewrite a historical event or impersonate this specific task.
        bindings = json.loads(BINDINGS.read_text()) if BINDINGS.exists() else {}
        if goal and tid not in bindings and goal['id'] in bindings:
            bindings = {**bindings, tid: bindings[goal['id']]}
        linked, link_note = link_project_step('\n'.join(lines), link_event, bindings)
        lines = linked.splitlines()
        label = f'#### [TASK:{tid}] {status}; {event["at"]}; exit={code}; bewijs {key}.json'
        if status in {'failed','interrupted','cancelled','blocked'}:
            label += '; RCCAP: uitvoering niet geslaagd; controleer resultaat; handmatig vervolg, geen retry'
        elif status == 'succeeded':
            if acceptance:
                label += '; worker afgerond; inhoudelijk geaccepteerd ' + ' '.join(acceptance)
            else:
                label += '; worker afgerond; inhoudelijke beoordeling blijft open'
        label += '; ' + link_note
        insert = lines.index(anchor) + 1
        while insert < len(lines) and (not lines[insert].strip() or lines[insert].startswith('####')):
            insert += 1
        branch = [label]
        retained = [child for child in children if child.startswith(f'##### [RCCAP:{tid}] ')]
        if status != 'succeeded':
            branch.append(f'##### [TEMP:{tid}] Technische uitvoering — bewaren zolang taak open is')
        branch.extend(retained)
        lines[insert:insert] = branch
        after = reconcile('\n'.join(lines).rstrip() + '\n')
        paths_after = nodes(after)
        def changes(a, b):
            return [{'step': n, 'heading': line} for line, n in a.items() if line not in b]
        record = {'event': event, 'nodes_before': len(paths_before), 'nodes_after': len(paths_after),
                  'removed': changes(paths_before, paths_after), 'added': changes(paths_after, paths_before),
                  'before_sha256': hashlib.sha256(before.encode()).hexdigest(),
                  'after_sha256': hashlib.sha256(after.encode()).hexdigest(),
                  'source_before': before, 'source_after': after,
                  'note': 'Only TEMP child pruned on succeeded after durable evidence; failed/open work and TASK receipt retained; success is worker status only.'}
        # Durable intent/preimage precedes any source/pruning mutation. On retry the
        # existing intent is kept; a conflicting source fails closed.
        intent = EVIDENCE / (key + '.pending.json')
        if intent.exists():
            pending = json.loads(intent.read_text())
            if pending['event'] != event or before not in {pending['source_before'], pending['source_after']}:
                raise ValueError('Pending publication source conflict')
            record = pending
            after = pending['source_after']
        else:
            atomic(intent, json.dumps(record, ensure_ascii=False, indent=2))
        with tempfile.TemporaryDirectory(dir=EVIDENCE) as work:
            candidate, output = Path(work)/'source.md', Path(work)/'map.json'
            candidate.write_text(after)
            env = dict(os.environ, CURRENT_PROJECTS_SOURCE=str(candidate), MAP_OUTPUT=str(output))
            subprocess.run(['node', 'build.mjs'], cwd=ROOT/'mindmap', env=env,
                           check=True, timeout=45, stdout=subprocess.DEVNULL)
            if SOURCE.read_text() != before:
                raise ValueError('Source changed during build')
            payload = output.read_bytes()
            atomic(SOURCE, after)
            atomic(MAP, payload)
            record['map_sha256'] = hashlib.sha256(payload).hexdigest()
            atomic(receipt, json.dumps(record, ensure_ascii=False, indent=2))
