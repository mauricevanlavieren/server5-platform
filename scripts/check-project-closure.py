"""One targeted regression, no database access or live mutations."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'web'))
import mindmap_lifecycle as lc


def check():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        evidence = root / 'docs/mindmaps'
        evidence.mkdir(parents=True)
        receipt = evidence / 'receipt.json'
        receipt.write_text(json.dumps({'event': {'task_id': 'fixture_task_0001', 'status': 'succeeded', 'exit_code': 0}}))
        acceptance = evidence / 'acceptance.json'
        acceptance.write_text(json.dumps({'project_id': 'P', 'outcome': 'project_finished', 'accepted': True}))
        active = '# Map\n## [PROJECT:P] [ACTIEF]\n### [STEP:S] 🔄 HUIDIGE STAP — uitvoeren\n'
        rule = {'id': 'TEST', 'project_id': 'P', 'step_id': 'S', 'outcome': 'project_finished',
                'task_id': 'fixture_task_0001', 'receipt': 'docs/mindmaps/receipt.json',
                'project_acceptance': 'docs/mindmaps/acceptance.json',
                'proofs': [{'path': str(p.relative_to(root)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in (receipt, acceptance)],
                'changes': [{'id': 'PROJECT:P', 'before': '## [PROJECT:P] [ACTIEF]', 'after': '## [PROJECT:P] [VOLTOOID]'},
                            {'id': 'STEP:S', 'before': '### [STEP:S] 🔄 HUIDIGE STAP — uitvoeren', 'after': '### [STEP:S] [ACCEPTED:TEST] ✅ gesloten'}]}
        waiting = active.replace('[ACTIEF]', '[WACHTEND]').replace('🔄 HUIDIGE STAP', '⏳ review nodig')
        with patch.object(lc, 'ROOT', root):
            closed = lc.reconcile(active, [rule])
            assert lc.reconcile(closed, [rule]) == closed
            assert lc.reconcile(active, []) == active  # success alone has no project authority
            assert lc.reconcile(waiting, []) == waiting
            bad = dict(rule, project_acceptance=None)
            try:
                lc.reconcile(active, [bad])
                raise AssertionError('Missing whole-project proof accepted')
            except ValueError:
                pass
        # All three outcomes pass the actual build/current-step invariant guard.
        for index, source in enumerate((closed, active, waiting)):
            candidate = root / f'{index}.md'
            candidate.write_text(source)
            subprocess.run(['node', 'build.mjs'], cwd=ROOT / 'mindmap',
                           env=dict(os.environ, CURRENT_PROJECTS_SOURCE=str(candidate), MAP_OUTPUT=str(root / f'{index}.json')),
                           check=True, stdout=subprocess.DEVNULL)
        acceptance.write_text('{}')
        with patch.object(lc, 'ROOT', root):
            try:
                lc.reconcile(active, [rule])
                raise AssertionError('Changed evidence accepted')
            except ValueError:
                pass
    return {'project_finished': 'PASS', 'unfinished_active': 'PASS', 'waiting': 'PASS',
            'missing_or_changed_acceptance_rejected': 'PASS', 'real_build_guard': 'PASS'}

if __name__ == '__main__':
    print(json.dumps(check()))
