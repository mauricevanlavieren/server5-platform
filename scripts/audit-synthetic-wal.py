#!/usr/bin/env python3
"""Audit SQLite WAL on disposable synthetic data only; never opens the broker."""
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile


def audit():
    with tempfile.TemporaryDirectory(prefix='server5-synthetic-wal-') as folder:
        path = Path(folder) / 'synthetic.sqlite3'
        writer = sqlite3.connect(path)
        reader = None
        try:
            writer.execute('PRAGMA journal_mode=WAL')
            writer.execute('PRAGMA wal_autocheckpoint=0')
            writer.execute('CREATE TABLE tasks(id TEXT PRIMARY KEY,status TEXT,exit_code INTEGER,prompt TEXT)')
            writer.execute('INSERT INTO tasks VALUES(?,?,?,?)',
                           ('synthetic_task_001', 'queued', None, 'SYNTHETIC_SENTINEL'))
            writer.commit()

            def snapshot():
                return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in Path(folder).iterdir()}

            before = snapshot()
            reader = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=1)
            reader.execute('PRAGMA query_only=ON')

            def authorize(action, table, column, *_):
                if action == sqlite3.SQLITE_SELECT:
                    return sqlite3.SQLITE_OK
                if action == sqlite3.SQLITE_READ and table == 'tasks' and column in {'id', 'status', 'exit_code'}:
                    return sqlite3.SQLITE_OK
                return sqlite3.SQLITE_DENY

            reader.execute('BEGIN')
            reader.set_authorizer(authorize)
            initial = reader.execute('SELECT id,status,exit_code FROM tasks WHERE id=?',
                                     ('synthetic_task_001',)).fetchone()
            writer.execute("UPDATE tasks SET status='running'")
            writer.commit()
            # The transaction must retain the original committed snapshot.
            stable = reader.execute('SELECT id,status,exit_code FROM tasks WHERE id=?',
                                    ('synthetic_task_001',)).fetchone()
            denied = []
            for name, sql in [('prompt', 'SELECT prompt FROM tasks'),
                              ('write', "UPDATE tasks SET status='failed'"),
                              ('schema', 'SELECT sql FROM sqlite_master')]:
                try:
                    reader.execute(sql).fetchall()
                except sqlite3.DatabaseError:
                    denied.append(name)
            reader.set_authorizer(None)
            reader.rollback()
            fresh = reader.execute('SELECT id,status,exit_code FROM tasks WHERE id=?',
                                   ('synthetic_task_001',)).fetchone()
            reader.close()
            reader = None
            # Writer activity above changes WAL too. Use a separate, idle-writer
            # observation to attribute sidecar changes exclusively to the reader.
            writer.execute("UPDATE tasks SET status='succeeded',exit_code=0")
            writer.commit()
            idle_before = snapshot()
            reader = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=1)
            reader.execute('PRAGMA query_only=ON')
            terminal = reader.execute('SELECT id,status,exit_code FROM tasks WHERE id=?',
                                      ('synthetic_task_001',)).fetchone()
            reader.close()
            reader = None
            idle_after = snapshot()
            changed = sorted(name for name in idle_before if idle_before[name] != idle_after.get(name))
            added = sorted(set(idle_after) - set(idle_before))
            return {'schema_version': 1, 'synthetic_only': True,
                    'sqlite_version': sqlite3.sqlite_version,
                    'metadata_columns': ['id', 'status', 'exit_code'],
                    'snapshot_consistent': initial == stable and initial[1] == 'queued',
                    'fresh_status': fresh[1], 'terminal_status': terminal[1],
                    'denied': denied, 'initial_files': sorted(before),
                    'idle_reader_changed': changed, 'idle_reader_added': added,
                    'filesystem_readonly_proven': False,
                    'live_export_allowed': False,
                    'decision': 'RCCAP: mode=ro does not establish filesystem read-only WAL access'}
        finally:
            if reader is not None:
                reader.close()
            writer.close()


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2))
