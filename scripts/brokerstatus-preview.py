#!/usr/bin/env python3
"""Local metadata snapshot to lifecycle proposal; stdout only, never applies changes."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs/mindmaps/import-current-projects.md'
STEPS = {'queued': 'wacht op uitvoering', 'running': 'uitvoering loopt',
         'succeeded': 'worker afgerond; menselijke resultaatbeoordeling pending',
         'failed': 'RCCAP: oorzaak onderzoeken; correctie bepalen; volgende actie handmatig kiezen'}


def local_file(ref, base=ROOT):
    if not isinstance(ref, str):
        raise ValueError('Invalid local reference')
    path = (base / ref).resolve()
    if not path.is_relative_to((base / 'docs/mindmaps').resolve()) or not path.is_file():
        raise ValueError('Reference outside local evidence directory')
    return path


def propose(source, metadata, binding, evidence=None, *, now=None, base=ROOT):
    if not isinstance(metadata, dict) or set(metadata) != {'id', 'status', 'exit_code'}:
        raise ValueError('Only id/status/exit_code metadata accepted; no worker output')
    tid, status = metadata['id'], metadata['status']
    if not isinstance(tid, str) or not re.fullmatch(r'[A-Za-z0-9_-]{16,80}', tid):
        raise ValueError('Invalid broker task ID')
    if status not in STEPS:
        raise ValueError('Unsupported status; never retry unknown/interrupted tasks')
    code = metadata['exit_code']
    if code is not None and type(code) is not int:
        raise ValueError('Invalid exit code')
    if not isinstance(binding, dict) or set(binding) != {'task_id', 'source_sha256', 'target', 'observed_at'}:
        raise ValueError('Invalid binding')
    headings = [line for line in source.splitlines() if line.strip()]
    if not headings or any(not re.fullmatch(r'#{1,6} .+', line) for line in headings):
        raise ValueError('Invalid Markdown')
    target = binding['target']
    if not isinstance(target, str) or headings.count(target) != 1 or not target.startswith('### '):
        raise ValueError('Unique level-three Workflow target required')
    index = headings.index(target)
    section = next((h for h in reversed(headings[:index]) if h.startswith('## ')), None)
    if section != '## Workflow':
        raise ValueError('Protected project branch')
    # A replacement of a leaf preserves all other task branches.
    if index + 1 < len(headings) and headings[index + 1].startswith('####'):
        raise ValueError('Target must be a leaf')
    digest = hashlib.sha256(source.encode()).hexdigest()
    blockers = []
    if binding['task_id'] != tid or binding['source_sha256'] != digest:
        blockers.append('task/source hash binding mismatch')
    try:
        observed = datetime.fromisoformat(binding['observed_at'].replace('Z', '+00:00'))
        if observed.utcoffset() != timezone.utc.utcoffset(observed):
            raise ValueError('UTC required')
        age = ((now or datetime.now(timezone.utc)) - observed).total_seconds()
        if not 0 <= age <= 300:
            blockers.append('observation stale or future')
    except (ValueError, TypeError, AttributeError):
        raise ValueError('Invalid UTC observation') from None
    if (status == 'succeeded' and code != 0) or (status in {'queued', 'running'} and code is not None):
        blockers.append('status/exit code contradiction')
    if status == 'failed':
        blockers.append('worker failed; manual RCCAP required')
    if status == 'succeeded':
        valid = False
        if isinstance(evidence, dict) and set(evidence) == {'task_id', 'source_sha256', 'result_ref', 'result_sha256', 'test_command', 'outcome'}:
            try:
                artifact = local_file(evidence['result_ref'], base)
                valid = (evidence['task_id'] == tid and evidence['source_sha256'] == digest
                         and evidence['outcome'] == 'pass' and isinstance(evidence['test_command'], str)
                         and bool(evidence['test_command'].strip())
                         and hashlib.sha256(artifact.read_bytes()).hexdigest() == evidence['result_sha256'])
            except (ValueError, OSError):
                pass
        if not valid:
            blockers.append('missing or invalid independently supplied test/result evidence')
    return {'schema_version': 1, 'task_id': tid, 'status': status,
            'observed_at': binding['observed_at'], 'source_sha256': digest,
            'target': target, 'current_step': STEPS[status],
            'proposed_heading': f'### Codex-taak — {tid}; {status}; {binding["observed_at"]}; {STEPS[status]}',
            'nodes_before': len(headings), 'nodes_after': len(headings), 'expected_node_delta': 0,
            'action': 'RCCAP' if blockers else 'preview_only', 'blockers': blockers,
            'rccap': {'cause': '; '.join(blockers), 'correction': 'controleer metadata, bronbinding en bewijs',
                      'next_step': 'maak na controle een nieuw voorstel; niet automatisch toepassen'} if blockers else None,
            'evidence_ref': evidence.get('result_ref') if status == 'succeeded' and not blockers else None,
            'preview_only': True, 'apply_authorized': False, 'acceptance': 'pending',
            'requires_human_review': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('metadata', 'binding', 'evidence'):
        parser.add_argument('--' + name, required=name != 'evidence')
    args = parser.parse_args()
    try:
        def read(ref):
            return json.loads(local_file(ref).read_text())
        result = propose(SOURCE.read_text(), read(args.metadata), read(args.binding),
                         read(args.evidence) if args.evidence else None)
    except (ValueError, OSError, TypeError):
        parser.exit(2, 'Proposal rejected: invalid local input or unavailable source\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
