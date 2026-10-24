#!/usr/bin/env python3
"""Read-only proposal from reviewed structured task data; never execute task output."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs/mindmaps/import-current-projects.md'


def preview(source, task, evidence):
    if not isinstance(task, dict) or not isinstance(evidence, dict):
        raise ValueError('Expected structured objects')
    if set(task) - {'id', 'status', 'target', 'source_sha256', 'split_count'}:
        raise ValueError('Unexpected task fields; free-form output is not accepted')
    tid = task.get('id')
    if not isinstance(tid, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', tid):
        raise ValueError('Invalid task ID')
    status = task.get('status')
    if status not in {'queued', 'running', 'succeeded', 'failed', 'cancelled', 'interrupted'}:
        raise ValueError('Invalid task status')
    headings = [line for line in source.splitlines() if line.strip()]
    if not headings or any(not re.fullmatch(r'#{1,6} .+', h) for h in headings):
        raise ValueError('Invalid source headings')
    target = task.get('target')
    if not isinstance(target, str) or headings.count(target) != 1:
        raise ValueError('Target must identify exactly one existing heading')
    index = headings.index(target)
    level = len(target.split(' ', 1)[0])
    end = index + 1
    while end < len(headings) and len(headings[end].split(' ', 1)[0]) > level:
        end += 1
    digest = hashlib.sha256(source.encode()).hexdigest()
    bound = task.get('source_sha256') == digest
    # Review is a separately supplied human assertion, never inferred from worker prose.
    reviewed = (set(evidence) == {'task_id', 'source_sha256', 'reviewed', 'tests_passed'}
                and evidence.get('task_id') == tid
                and evidence.get('source_sha256') == digest
                and evidence.get('reviewed') is True
                and evidence.get('tests_passed') is True)
    action, delta, reason = 'RCCAP', 0, 'Taakcontrole/bewijs ontbreekt of taak is niet afgerond'
    if bound and reviewed and status == 'succeeded':
        section = next((h for h in reversed(headings[:index]) if h.startswith('## ')), None)
        if target.startswith('#### Tijdelijke implementatie — ') and section == '## Workflow':
            action, delta, reason = 'snoeien', -(end - index), 'Alleen geselecteerde tijdelijke branch; menselijke uitvoering vereist'
        else:
            reason = 'Snoeien beperkt tot tijdelijke implementatiebranch onder Workflow'
    elif bound and reviewed and status in {'queued', 'running'}:
        count = task.get('split_count')
        if type(count) is int and 1 <= count <= 10 and level < 6:
            action, delta, reason = 'vertakken', count, 'Voorgesteld aantal nieuwe directe subtaken'
    return {'task_id': tid, 'status': status, 'current_step': target,
            'source_sha256': digest, 'expected_node_delta': delta,
            'nodes_before': len(headings), 'nodes_after': len(headings) + delta,
            'action': action, 'reason': reason, 'preview_only': True,
            'requires_human_review': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True,
                        help='Separately reviewed structured evidence; not raw worker output')
    args = parser.parse_args()
    try:
        # Only explicitly supplied JSON documents are read; no DB, auth or log discovery.
        result = preview(SOURCE.read_text(), json.loads(args.task.read_text()),
                         json.loads(args.evidence.read_text()))
    except (ValueError, OSError, TypeError):
        parser.exit(2, 'Preview rejected: invalid input or unavailable source\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
