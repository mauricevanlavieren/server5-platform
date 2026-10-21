"""Recovery tests never use a production database, credential or service."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sqlite3
import sys
import tarfile
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import recovery


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.source = self.base / 'source.sqlite3'
        with contextlib.closing(sqlite3.connect(self.source)) as db:
            db.executescript('PRAGMA journal_mode=WAL; CREATE TABLE tasks(id TEXT PRIMARY KEY,status TEXT,prompt TEXT);'
                'CREATE TABLE events(seq INTEGER PRIMARY KEY,task TEXT,text TEXT);'
                'CREATE TABLE sessions(id TEXT,csrf TEXT);')
            db.execute('INSERT INTO tasks VALUES(?,?,?)', ('A'*20, 'queued', 'Mock only'))
            db.execute('INSERT INTO events VALUES(?,?,?)', (1, 'A'*20, 'Fixture event'))
            self.session = 'SESSION-SENSITIVE-' + 'Q'*50
            db.execute('INSERT INTO sessions VALUES(?,?)', ('id', self.session)); db.commit()
        self.snapshot = self.base / 'snapshot.sqlite3'
        summary = recovery.snapshot_database(self.source, self.snapshot)
        self.payload = {'project/' + name: b'# safe\n' for name in recovery.REQUIRED}
        self.payload['data/tasks.sqlite3'] = self.snapshot.read_bytes()
        self.manifest = {'format': 1, 'database': summary,
            'entries': {name: {'sha256': recovery.digest(data), 'size': len(data), 'mode':0o600, 'original_mode':0o644}
                        for name, data in self.payload.items()}}
        self.folder = self.base / 'backups';self.folder.mkdir(mode=0o700)
    def tearDown(self): self.temp.cleanup()
    def bundle(self): return recovery.write_bundle(self.folder, self.payload, self.manifest)
    def test_roundtrip_private_and_no_execution(self):
        self.payload['project/web/commandcenter.py'] = b'raise RuntimeError("MUST NOT EXECUTE")\n'
        e = self.manifest['entries']['project/web/commandcenter.py']
        e.update(sha256=recovery.digest(self.payload['project/web/commandcenter.py']),size=len(self.payload['project/web/commandcenter.py']))
        archive = self.bundle()
        result = recovery.restore_test(archive)
        self.assertEqual(result['tasks'],1);self.assertFalse(result['production_data_touched'])
        self.assertEqual(archive.stat().st_mode & 0o777,0o600)
        self.assertEqual(archive.with_suffix('.sha256').stat().st_mode & 0o777,0o600)
        out = self.base / 'restore';out.mkdir()
        recovery.validate_into(archive,out)
        self.assertTrue(all(p.stat().st_mode & 0o077 == 0 for p in out.rglob('*')))
    def test_sessions_scrubbed_and_source_untouched(self):
        self.assertNotIn(self.session.encode(),self.snapshot.read_bytes())
        with contextlib.closing(sqlite3.connect(self.source)) as db:
            self.assertEqual(db.execute('SELECT csrf FROM sessions').fetchone()[0],self.session)
            self.assertEqual(db.execute('SELECT status FROM tasks').fetchone()[0],'queued')
        self.assertFalse(Path(str(self.snapshot)+'-wal').exists())
    def test_wal_commits_included(self):
        with contextlib.closing(sqlite3.connect(self.source)) as db:
            db.execute('INSERT INTO tasks VALUES(?,?,?)',('B'*20,'succeeded','Recent'));db.commit()
            other = self.base/'recent.sqlite3'
            summary = recovery.snapshot_database(self.source,other)
            self.assertEqual(summary['tasks']['count'],2)
    def test_corrupt_checksum_rejected(self):
        p=self.bundle();p.write_bytes(p.read_bytes()+b'x')
        with self.assertRaisesRegex(ValueError,'Checksum mismatch'): recovery.restore_test(p)
    def test_corrupt_manifest_hash_rejected(self):
        self.manifest['entries']['data/tasks.sqlite3']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'payload mismatch'):recovery.restore_test(self.bundle())
    def test_missing_required_file_rejected(self):
        del self.payload['project/web/app.js'];del self.manifest['entries']['project/web/app.js']
        with self.assertRaisesRegex(ValueError,'Incomplete'):recovery.restore_test(self.bundle())
    def test_duplicate_traversal_links_and_devices_rejected(self):
        for name,kind in [('../escape',tarfile.REGTYPE),('/tmp/escape',tarfile.REGTYPE),
                          ('link',tarfile.SYMTYPE),('device',tarfile.CHRTYPE),('same',tarfile.REGTYPE)]:
            with self.subTest(name=name), tempfile.TemporaryDirectory(dir=self.base) as td:
                path=Path(td)/'recovery-bad.tar.gz'
                with tarfile.open(path,'w:gz') as tf:
                    m=tarfile.TarInfo(name);m.type=kind;m.mode=0o600;tf.addfile(m)
                    if name=='same':tf.addfile(m)
                path.chmod(0o600)
                side=path.with_suffix('.sha256');side.write_text(recovery.digest(path.read_bytes()));side.chmod(0o600)
                with self.assertRaises(ValueError):recovery.restore_test(path)
    def test_nonempty_restore_destination_rejected(self):
        out=self.base/'production';out.mkdir();(out/'keep').write_text('unchanged')
        with self.assertRaisesRegex(ValueError,'new empty'):recovery.validate_into(self.bundle(),out)
        self.assertEqual((out/'keep').read_text(),'unchanged')
    def test_budget_preserves_all_previous_backups(self):
        p=self.bundle();before=p.read_bytes()
        with self.assertRaisesRegex(ValueError,'budget'): recovery.write_bundle(self.folder,self.payload,self.manifest,budget=1)
        self.assertEqual(p.read_bytes(),before)
        self.assertFalse(list(self.folder.glob('.bundle-*')))
    def test_source_secret_detection(self):
        for value in [b'sk-'+b'A'*40,b'ghp_'+b'Z'*40,b'-----BEGIN '+b'PRIVATE KEY-----',b'local-owner-credential']:
            with self.assertRaises(ValueError):recovery.scan_source(value,forbidden=[b'local-owner-credential'])
    def test_private_permissions_and_symlink(self):
        path=self.base/'credential';path.write_text('synthetic');path.chmod(0o644)
        with self.assertRaises(ValueError):recovery.regular(path,private=True)
        link=self.base/'link';link.symlink_to(path)
        with self.assertRaises(OSError):recovery.regular(link)
    def test_database_manifest_tampering_rejected(self):
        self.manifest['database']['events']['count']=99
        with self.assertRaisesRegex(ValueError,'database differs'):recovery.restore_test(self.bundle())
    def test_untracked_sources_included_and_inventory_excluded(self):
        import subprocess
        repo=self.base/'repo';repo.mkdir()
        subprocess.run(['git','init','-q',str(repo)],check=True)
        for name in recovery.REQUIRED:
            path=repo/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('# fixture')
        (repo/'inventory').mkdir();(repo/'inventory/private.json').write_text('not for archive')
        self.assertIn('web/app.js',recovery.source_files(repo))
        self.assertNotIn('inventory/private.json',recovery.source_files(repo))


if __name__=='__main__':unittest.main()
