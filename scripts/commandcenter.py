#!/usr/bin/env python3
"""Local host checks and committed-configuration recovery; never runs remote tasks."""
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
    mem = {}
    for line in Path('/proc/meminfo').read_text().splitlines():
        name, value = line.split(':', 1)
        mem[name] = int(value.split()[0]) * 1024
    disk = shutil.disk_usage('/')
    failed = run('systemctl', '--failed', '--no-legend', '--plain', '--no-pager')
    ssh = run('systemctl', 'is-active', 'ssh')
    ntp = run('timedatectl', 'show', '-p', 'NTPSynchronized', '--value')
    alerts = []
    if mem['MemAvailable'] < 2 * 1024**3:
        alerts.append('available_memory_below_2GiB')
    if disk.free < 15 * 1024**3:
        alerts.append('root_free_below_15GiB')
    if failed.returncode or failed.stdout.strip():
        alerts.append('system_units_failed_or_unknown')
    if ssh.stdout.strip() != 'active':
        alerts.append('ssh_not_active')
    if ntp.stdout.strip() != 'yes':
        alerts.append('ntp_not_synchronized_or_unknown')
    result = {
        'utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'hostname': socket.gethostname(), 'load': os.getloadavg(),
        'memory_available_bytes': mem['MemAvailable'], 'root_free_bytes': disk.free,
        'ssh_active': ssh.stdout.strip(), 'ntp_synchronized': ntp.stdout.strip(),
        'failed_units': failed.stdout.splitlines(),
        'reboot_required': Path('/var/run/reboot-required').exists(),
        'tools_present': {x: bool(shutil.which(x)) for x in ['bwrap', 'tailscale', 'docker']},
        'alerts': alerts,
    }
    payload = (json.dumps(result, sort_keys=True) + '\n').encode()
    atomic(STATE / 'latest.json', payload)
    history = STATE / ('health-' + dt.date.today().isoformat() + '.jsonl')
    total = sum(p.stat().st_size for p in STATE.glob('health-*.jsonl'))
    if total + len(payload) <= 128 * 1024**2 and (not history.exists() or history.stat().st_size + len(payload) <= 1024**2):
        with history.open('ab') as f:
            f.write(payload)
        history.chmod(0o600)
    else:
        result['alerts'].append('history_budget_reached')
        atomic(STATE / 'latest.json', (json.dumps(result) + '\n').encode())
    print(json.dumps(result))
    return bool(result['alerts'])


def backup():
    if run('git', '-C', str(ROOT), 'status', '--porcelain').stdout.strip():
        raise ValueError('Commit reviewed changes first; backup only includes clean Git HEAD')
    commit = git('rev-parse', 'HEAD').decode().strip()
    BACKUPS.mkdir(mode=0o700, parents=True, exist_ok=True)
    archive = git('archive', '--format=tar.gz', 'HEAD')
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz') as tf:
        checked_members(tf)
    path = BACKUPS / (commit + '.tar.gz')
    digest = hashlib.sha256(archive).hexdigest()
    if path.exists():
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('Existing backup differs; preserve for diagnosis')
    else:
        if sum(p.stat().st_size for p in BACKUPS.iterdir() if p.is_file()) + len(archive) > 256 * 1024**2:
            raise ValueError('Backup budget reached; no files deleted')
        atomic(path, archive)
    atomic(path.with_suffix('.sha256'), (digest + '\n').encode())
    print(json.dumps({'archive': str(path), 'commit': commit, 'sha256': digest,
                      'scope': 'committed configuration only; no OS, credentials or workload data'}))
    return False


def restore_test(path):
    path = Path(path).resolve()
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
