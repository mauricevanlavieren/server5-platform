#!/usr/bin/env python3
"""Server5 credential-free metadata recovery. No credential or worker-text reads."""
import contextlib
import datetime
import fcntl
import json
import os
from pathlib import Path
import re
import socket
import sqlite3
import subprocess
import tempfile
import urllib.request
import recovery as r

ROOT = Path(__file__).resolve().parents[1]
TASK = 'server5_recovery_mvp_20261022_001'
OUT = ROOT / 'docs/mindmaps/server5-recovery-mvp-20261022'

def main():
    assert socket.gethostname() == 'server5'
    OUT.mkdir(exist_ok=True)
    payload, entries = {}, {}
    def add(name, data):
        r.scan_source(data)
        payload[name] = data
        entries[name] = dict(sha256=r.digest(data), size=len(data), mode=0o600, original_mode=0o600)
    paths = set(r.REQUIRED)
    paths.update(str(p.relative_to(ROOT)) for p in (ROOT/'web').glob('*.py') if '.bak' not in p.name)
    paths.update(['mindmap/'+s for s in ['build.mjs','current-step.mjs','viewer.js','serve.py','package.json','package-lock.json','public/index.html','public/viewer.js','public/map.json']])
    paths.update(['docs/mindmaps/import-current-projects.md','docs/mindmaps/import-server5-commandcenter.md','docs/mindmaps/project-closures.json','scripts/recovery-mvp.py','docs/mvp-runbook.md','systemd/user/server5-mindmap.service'])
    rules=json.loads((ROOT/'docs/mindmaps/project-closures.json').read_text())
    for rule in rules:
        paths.update(p['path'] for p in rule['proofs'])
    paths.update(str(p.relative_to(ROOT)) for p in (ROOT/'docs/mindmaps/live-lifecycle').glob('broker-*.json') if '.pending.' not in p.name)
    with tempfile.TemporaryDirectory(prefix='s5-metadata-') as td:
        td=Path(td)
        with (ROOT/'docs/mindmaps/live-lifecycle/writer.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            for p in sorted(paths):
                data,_=r.regular(ROOT/p)
                add('project/'+p,data)
            # Whitelisted SELECT only; no prompts/results/events/auth/session values read.
            uri=(Path.home()/'.local/state/server5-commandcenter/mvp/tasks.sqlite3').as_uri()+'?mode=ro'
            with contextlib.closing(sqlite3.connect(uri,uri=True,timeout=3)) as src:
                src.execute('PRAGMA query_only=ON'); src.execute('BEGIN')
                columns='id,parent,status,created,started,finished,exit_code,cancel,log_bytes'
                rows=src.execute('SELECT '+columns+' FROM tasks ORDER BY id').fetchall()
                outbox=src.execute('SELECT seq,task_id,status,exit_code,at,delivered FROM mindmap_outbox ORDER BY seq').fetchall()
                src.rollback()
            assert all(re.fullmatch(r'[A-Za-z0-9_-]{1,100}',row[0]) and row[2] in {'queued','running','succeeded','failed','cancelled','interrupted'} for row in rows)
            assert all(row[1] is None or re.fullmatch(r'[A-Za-z0-9_-]{1,100}',row[1]) for row in rows)
            dbpath=td/'tasks.sqlite3'
            with sqlite3.connect(dbpath) as dest:
                dest.executescript('CREATE TABLE tasks(id TEXT PRIMARY KEY,prompt TEXT NOT NULL,parent TEXT,status TEXT NOT NULL,created REAL NOT NULL,started REAL,finished REAL,result TEXT DEFAULT "",exit_code INTEGER,cancel INTEGER DEFAULT 0,log_bytes INTEGER DEFAULT 0); CREATE TABLE events(seq INTEGER PRIMARY KEY AUTOINCREMENT,task TEXT NOT NULL,at REAL NOT NULL,text TEXT NOT NULL); CREATE TABLE sessions(id TEXT PRIMARY KEY,csrf TEXT NOT NULL,expires REAL NOT NULL); CREATE TABLE mindmap_outbox(seq INTEGER PRIMARY KEY,task_id TEXT,status TEXT,exit_code INTEGER,at TEXT,delivered INTEGER);')
                dest.executemany('INSERT INTO tasks('+columns+',prompt) VALUES(?,?,?,?,?,?,?,?,?,?)',[tuple(row)+('[omitted: metadata recovery; never execute]',) for row in rows])
                dest.executemany('INSERT INTO mindmap_outbox VALUES(?,?,?,?,?,?)',outbox)
                dest.commit()
                summary=r.db_summary(dest)
            add('data/tasks.sqlite3',dbpath.read_bytes())
            add('data/lifecycle.json',json.dumps(outbox,separators=(',',':')).encode())
            assert all(r.digest(r.regular(ROOT/p)[0])==entries['project/'+p]['sha256'] for p in paths)
        policy='Metadata-only registry recovery: preserves IDs, parent, status, timestamps, exit codes and outbox. Prompts/results/event text/auth/sessions deliberately excluded and never selected. NOT a runnable production DB replacement. Never start workers/services from restored state; queued/running are historical unresolved and require owner reconciliation. Existing host credentials/runtime required. No automatic replay. Snapshot records this task running; terminal receipt follows worker exit.'
        add('RESTORE-POLICY.txt',policy.encode())
        manifest=dict(format=1,hostname='server5',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),entries=entries,database=summary,task_id=TASK,scope=policy,lifecycle_sha256=entries['data/lifecycle.json']['sha256'],runtime={'python':subprocess.check_output(['python3','--version'],text=True).strip(),'node':subprocess.check_output(['node','--version'],text=True).strip(),'dependencies':'project/mindmap/package-lock.json and project/requirements-mcp.lock; node_modules/venv not archived'},git_head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
        folder=Path.home()/'.local/share/server5-commandcenter/mvp-recovery'
        archive=r.write_bundle(folder,payload,manifest)
        with tempfile.TemporaryDirectory(prefix='s5-isolated-restore-') as restore:
            restored=r.validate_into(archive,Path(restore))
            project=Path(restore)/'project'
            for p in project.rglob('*.py'): compile(p.read_bytes(),str(p),'exec')
            (project/'mindmap/node_modules').symlink_to(ROOT/'mindmap/node_modules',target_is_directory=True)
            built=Path(restore)/'rebuilt.json'
            subprocess.run(['node','build.mjs'],cwd=project/'mindmap',env=dict(os.environ,MAP_OUTPUT=str(built)),check=True)
            assert json.loads(built.read_bytes())==json.loads((project/'mindmap/public/map.json').read_bytes())
            dbfile=Path(restore)/'data/tasks.sqlite3'
            with sqlite3.connect(dbfile.as_uri()+'?mode=ro&immutable=1',uri=True) as db:
                assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
                assert db.execute('SELECT '+columns+' FROM tasks ORDER BY id').fetchall()==rows
                assert db.execute('SELECT * FROM mindmap_outbox ORDER BY seq').fetchall()==outbox
                assert db.execute('SELECT count(*) FROM tasks WHERE prompt != ? OR result != ""',('[omitted: metadata recovery; never execute]',)).fetchone()[0]==0
        result=dict(archive=str(archive),sha256=r.file_digest(archive),manifest_format=1,files=len(entries),tasks=len(rows),lifecycle_events=len(outbox),restore='PASS: checksum, safe extraction, all file hashes, read-only SQLite integrity and metadata equality, Python compile, isolated build equals publication',scope=policy)
        (OUT/'recovery-verification.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result,indent=2))

if __name__=='__main__': main()
