#!/usr/bin/env python3
"""Local host checks and private application recovery; never runs remote tasks."""
import argparse
import datetime as dt
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import socket
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
STATE = Path.home() / '.local/state/server5-commandcenter'
BACKUPS = Path.home() / '.local/share/server5-commandcenter/backups'


def run(*args):
    return subprocess.run(args, capture_output=True, text=True, timeout=20)


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], timeout=30)


def atomic(path, data):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as f:
        temp = Path(f.name)
        f.write(data)
    os.replace(temp, path)


def checked_members(archive):
    members = archive.getmembers()
    for member in members:
        path = PurePosixPath(member.name)
        if path.is_absolute() or '..' in path.parts or not (member.isfile() or member.isdir()):
            raise ValueError('Unsafe archive member: ' + member.name)
    return members


def status():
    from health import observe, record
    result = record(observe(), STATE, atomic)
    print(json.dumps(result, sort_keys=True))
    return result['exit_code']


def backup():
    from recovery import backup as bundle_backup
    try:
        print(json.dumps(bundle_backup()))
        return False
    except Exception:
        print('{"error":"Recoverybackup mislukt; beoordeel lokaal zonder secrets te delen"}')
        return True


def restore_test(path):
    path = Path(path).resolve()
    if path.name.startswith('recovery-'):
        from recovery import restore_test as bundle_restore_test
        print(json.dumps(bundle_restore_test(path)))
        return False
    expected = path.with_suffix('.sha256').read_text().strip()
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError('Checksum mismatch')
    commit = path.name.removesuffix('.tar.gz')
    # Validate the commit before using it as a git revision.
    if len(commit) != 40 or any(c not in '0123456789abcdef' for c in commit):
        raise ValueError('Archive filename must be its full commit SHA')
    tree = git('ls-tree', '-rz', '--full-tree', commit).split(b'\0')
    expected_files = {}
    for entry in tree:
        if entry:
            info, name = entry.split(b'\t', 1)
            mode, kind, oid = info.split()
            if kind != b'blob' or mode not in (b'100644', b'100755'):
                raise ValueError('Only regular versioned files supported')
            expected_files[name.decode()] = (git('cat-file', 'blob', oid.decode()), mode == b'100755')
    with tempfile.TemporaryDirectory(prefix='server5-restore-test-') as temp:
        dest = Path(temp)
        with tarfile.open(path, 'r:gz') as tf:
            checked_members(tf)
            tf.extractall(dest, filter='data')
        actual = {str(f.relative_to(dest)) for f in dest.rglob('*') if f.is_file()}
        if actual != set(expected_files):
            raise ValueError('Restored file set differs from Git')
        for name, (content, executable) in expected_files.items():
            file = dest / name
            if file.read_bytes() != content or bool(file.stat().st_mode & 0o111) != executable:
                raise ValueError('Restored file mismatch: ' + name)
    print(json.dumps({'restore_test': 'passed', 'files': len(expected_files),
                      'commit': commit, 'production_data_touched': False}))
    return False


def main():
    os.umask(0o077)
    if socket.gethostname() != 'server5':
        raise SystemExit('This automation is restricted to server5')
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['status', 'backup', 'restore-test'])
    parser.add_argument('archive', nargs='?')
    args = parser.parse_args()
    if args.action == 'restore-test' and not args.archive:
        parser.error('restore-test requires an archive path')
    if args.action == 'status':
        return status()
    if args.action == 'backup':
        return backup()
    return restore_test(args.archive)


if __name__ == '__main__':
    raise SystemExit(main())
