#!/usr/bin/env python3
"""Fixture-only read-only export prototype. No live broker integration."""
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path
import re
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests/fixtures/broker-metadata'


def export_fixture(path, task_id):
    path = Path(path).resolve()
    if not path.is_relative_to(FIXTURES.resolve()) or not path.is_file():
        raise ValueError('Fixture directory required')
    if not isinstance(task_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{16,80}', task_id):
        raise ValueError('Invalid task ID')
    # immutable is safe ONLY for closed synthetic fixtures; never use on live WAL.
    db = sqlite3.connect(path.as_uri() + '?mode=ro&immutable=1', uri=True, timeout=1)
    try:
        db.execute('PRAGMA query_only=ON')
        def authorize(action, table, column, *_):
            if action == sqlite3.SQLITE_SELECT:
                return sqlite3.SQLITE_OK
            if action == sqlite3.SQLITE_READ and table == 'tasks' and column in {'id', 'status', 'exit_code'}:
                return sqlite3.SQLITE_OK
            return sqlite3.SQLITE_DENY
        db.set_authorizer(authorize)
        rows = db.execute('SELECT id,status,exit_code FROM tasks WHERE id=? LIMIT 2', (task_id,)).fetchall()
        observed_at = datetime.now(timezone.utc).isoformat()
    finally:
        db.close()
    if len(rows) != 1:
        raise ValueError('Exactly one task required')
    tid, status, code = rows[0]
    if status not in {'queued', 'running', 'succeeded', 'failed'}:
        raise ValueError('Unsupported status')
    if code is not None and type(code) is not int:
        raise ValueError('Invalid exit code')
    if status in {'queued', 'running'} and code is not None or status == 'succeeded' and code != 0:
        raise ValueError('Contradictory status')
    return {'schema_version': 1, 'fixture_only': True, 'observed_at': observed_at,
            'metadata': {'id': tid, 'status': status, 'exit_code': code}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture', required=True)
    parser.add_argument('--task-id', required=True)
    args = parser.parse_args()
    try:
        result = export_fixture(args.fixture, args.task_id)
    except (ValueError, OSError, sqlite3.Error):
        parser.exit(2, 'Export rejected: invalid fixture or metadata\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
