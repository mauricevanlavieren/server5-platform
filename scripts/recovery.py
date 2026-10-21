#!/usr/bin/env python3
"""Private, offline-verifiable application recovery bundles; never starts services."""
import contextlib
import datetime as dt
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import socket
import sqlite3
import stat
import subprocess
import tarfile
import tempfile
import time

BUDGET = 256 * 1024**2
MAX_FILE = 16 * 1024**2
MAX_EXPANDED = 192 * 1024**2
SOURCE_DIRS = {'web', 'scripts', 'tests', 'systemd', 'docs', 'plans', 'templates', '.githooks'}
ROOT_FILES = {'AGENTS.md', 'README.md', '.gitignore', 'requirements-mcp.lock'}
REQUIRED = {'web/commandcenter.py', 'web/app.js', 'web/index.html', 'web/style.css',
            'web/mcp_adapter.py', 'requirements-mcp.lock', 'systemd/user/server5-commandcenter.service',
            'systemd/user/server5-mcp.service', 'systemd/user/server5-mcp-tunnel.service',
            'systemd/user/server5-task-backup.service', 'scripts/recovery.py'}
CREDENTIALS = ('mcp-token', 'mcp-authorization-header', 'tunnel-runtime-key')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def run(args):
    return subprocess.check_output(args, stderr=subprocess.DEVNULL, timeout=15)


def regular(path, private=False):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
            raise ValueError('Owner/regular-file check failed')
        if private and info.st_mode & 0o077:
            raise ValueError('Private file permissions too broad')
        data = stream.read(MAX_FILE + 1)
        if len(data) > MAX_FILE:
            raise ValueError('File exceeds recovery limit')
        return data, stat.S_IMODE(info.st_mode)


def scan_source(data, forbidden=()):
    # Do not print a match, filename, source line or subprocess stderr.
    if any(value and value in data for value in forbidden):
        raise ValueError('Credential detected; bundle refused')
    for pattern in [rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
                    rb'\bsk-(?:proj-)?[A-Za-z0-9_-]{35,}',
                    rb'\bgh[pousr]_[A-Za-z0-9]{30,}', rb'\btskey-auth-[A-Za-z0-9-]{20,}']:
        if re.search(pattern, data):
            raise ValueError('Possible source credential; bundle refused')


def source_files(root):
    names = set(run(['git', '-C', str(root), 'ls-files', '-co', '--exclude-standard', '-z']).decode().split('\0'))
    chosen = set()
    for name in names - {''}:
        parts = PurePosixPath(name).parts
        if '..' in parts or PurePosixPath(name).is_absolute():
            raise ValueError('Unsafe source path')
        if '__pycache__' in parts or name.endswith(('.pyc', '.pyo')):
            continue
        if parts[0] in SOURCE_DIRS or name in ROOT_FILES or name.startswith('config/'):
            if any(p in {'secrets', '.git', 'inventory'} for p in parts) or Path(name).suffix in {'.key', '.pem', '.sqlite3'} or Path(name).name.startswith('.env'):
                raise ValueError('Disallowed source path')
            chosen.add(name)
    if not REQUIRED <= chosen:
        raise ValueError('Required recovery source missing')
    return sorted(chosen)


def db_summary(db):
    if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
        raise ValueError('Database integrity check failed')
    if db.execute('PRAGMA foreign_key_check').fetchall():
        raise ValueError('Database foreign-key check failed')
    out = {}
    for table, order in [('tasks', 'id'), ('events', 'seq')]:
        rows = db.execute(f'SELECT * FROM {table} ORDER BY {order}').fetchall()
        out[table] = {'count': len(rows), 'sha256': digest(json.dumps(rows, ensure_ascii=True, separators=(',', ':')).encode())}
    out['statuses'] = dict(db.execute('SELECT status,count(*) FROM tasks GROUP BY status').fetchall())
    out['sessions'] = db.execute('SELECT count(*) FROM sessions').fetchone()[0]
    return out


def snapshot_database(source, target):
    # No Store constructor/recovery, checkpoint or write transaction on production.
    with contextlib.closing(sqlite3.connect(source.as_uri() + '?mode=ro', uri=True, timeout=3)) as src:
        src.execute('PRAGMA query_only=ON')
        with contextlib.closing(sqlite3.connect(target)) as dest:
            deadline = time.monotonic() + 15
            def progress(*args):
                if time.monotonic() > deadline:
                    raise TimeoutError('Snapshot deadline exceeded')
            src.backup(dest, pages=64, progress=progress, sleep=.01)
            dest.execute('PRAGMA secure_delete=ON')
            dest.execute('DELETE FROM sessions')
            dest.commit()
            # Self-contained file: no dependency on copied WAL/SHM.
            dest.execute('PRAGMA journal_mode=DELETE')
            dest.execute('VACUUM')
            summary = db_summary(dest)
    target.chmod(0o600)
    return summary


def runtime_manifest(home):
    venv = home / '.local/share/server5-commandcenter/mcp-venv/bin/python'
    packages = json.loads(run([str(venv), '-B', '-c',
        'import importlib.metadata,json; print(json.dumps(sorted((d.metadata["Name"],d.version) for d in importlib.metadata.distributions())))']))
    binaries = {}
    for name, path in [('python', Path('/usr/bin/python3')), ('node', Path(shutil.which('node') or '/missing')),
                       ('codex', Path(shutil.which('codex') or '/missing')),
                       ('tunnel-client', home / '.local/bin/tunnel-client')]:
        actual = path.resolve(strict=True)
        binaries[name] = {'path': str(path), 'resolved': str(actual), 'sha256': file_digest(actual)}
    return {'tunnel_client': run([str(home / '.local/bin/tunnel-client'), '--version']).decode().strip(),
            'python': run(['/usr/bin/python3', '--version']).decode().strip(),
            'node': run([str(Path(shutil.which('node'))), '--version']).decode().strip(),
            'codex': run([str(Path(shutil.which('codex'))), '--version']).decode().strip(),
            'packages': packages, 'binaries': binaries,
            'note': 'Binaries/venv/OS not archived; reuse verified host runtime or reprovision pinned dependencies. Never copy account login files.'}


def collect(root, home, temp):
    root, home = Path(root).resolve(), Path(home).resolve()
    config = home / '.config/server5-commandcenter'
    forbidden = [regular(config / name, private=True)[0].strip() for name in CREDENTIALS]
    forbidden.append(regular(home / '.local/state/server5-commandcenter/mvp/login-password.txt', private=True)[0].strip())
    payload, entries = {}, {}
    def add(name, data, original_mode=0o600, source=False):
        if source:
            scan_source(data, forbidden)
        elif any(value and value in data for value in forbidden):
            raise ValueError('Credential detected; bundle refused')
        mode = 0o700 if original_mode & 0o111 else 0o600
        payload[name] = data
        entries[name] = {'sha256': digest(data), 'size': len(data), 'mode': mode, 'original_mode': original_mode}
    names = source_files(root)
    original = {}
    unit_states = {}
    for name in names:
        if (root / name).resolve() != root / name:
            raise ValueError('Source symlink refused')
        data, mode = regular(root / name)
        add('project/' + name, data, mode, source=True)
        original[name] = (digest(data), mode)
    for name in sorted((root / 'systemd/user').glob('server5-*')):
        installed = home / '.config/systemd/user' / name.name
        if installed.is_symlink():
            if installed.resolve() != name.resolve():
                raise ValueError('Unexpected installed unit symlink')
            installed = installed.resolve()
        data, mode = regular(installed)
        add('installed-units/' + name.name, data, mode, source=True)
        state_check = subprocess.run(['systemctl', '--user', 'is-enabled', name.name], capture_output=True, text=True, timeout=5)
        state_value = state_check.stdout.strip()
        if state_value not in {'enabled', 'disabled', 'static', 'indirect', 'linked', 'enabled-runtime', 'masked'}:
            raise ValueError('Cannot record installed unit enablement')
        unit_states[name.name] = state_value
    data, mode = regular(home / 'AGENTS.md')
    add('host/AGENTS.md', data, mode, source=True)
    state = home / '.local/state/server5-commandcenter/mvp'
    data, mode = regular(state / 'public-origin.txt', private=True)
    if not re.fullmatch(rb'https://[a-zA-Z0-9.-]+\.ts\.net\s*', data):
        raise ValueError('Unexpected private origin')
    add('settings/public-origin.txt', data, mode, source=True)
    # Only copy the reviewed file-reference profile, never arbitrary inline keys.
    profile, mode = regular(config / 'tunnel.yaml', private=True)
    match = re.search(rb'tunnel_[a-f0-9]{32}', profile)
    template = (root / 'config/tunnel-client/server5.yaml.example').read_bytes()
    if not match or profile.strip() != template.replace(b'OWNER_EXISTING_TUNNEL_ID', match[0]).strip():
        raise ValueError('Tunnel profile differs from file-reference template; review required')
    add('settings/tunnel.yaml', profile, mode, source=True)
    serve = run(['tailscale', 'serve', 'status', '--json'])
    parsed = json.loads(serve)
    if parsed.get('AllowFunnel'):
        raise ValueError('Unexpected network exposure; stop')
    add('settings/tailscale-serve.json', serve, source=True)
    if (state / 'mcp-start-task.disabled').exists() or (state / 'mcp-start-task.disabled').is_symlink():
        add('settings/mcp-start-task.disabled', b'')
    summary = snapshot_database(state / 'tasks.sqlite3', temp / 'tasks.sqlite3')
    add('data/tasks.sqlite3', (temp / 'tasks.sqlite3').read_bytes())
    credentials = []
    for name in CREDENTIALS + ('tunnel.yaml',):
        path = config / name
        info = path.lstat()
        credentials.append({'path': str(path), 'uid': info.st_uid, 'mode': stat.S_IMODE(info.st_mode),
                            'contents_archived': name == 'tunnel.yaml'})
    for name in ['auth.json', 'login-password.txt']:
        path = state / name
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError('Web credential permissions invalid')
        credentials.append({'path': str(path), 'uid': info.st_uid, 'mode': stat.S_IMODE(info.st_mode), 'contents_archived': False})
    linger = run(['loginctl', 'show-user', str(os.getuid()), '-p', 'Linger', '--value']).decode().strip()
    if linger not in {'yes', 'no'}:
        raise ValueError('Cannot record linger')
    manifest = {'unit_enablement': unit_states, 'linger': linger, 'format': 1, 'hostname': socket.gethostname(), 'utc': dt.datetime.now(dt.timezone.utc).isoformat(),
                'git_head': run(['git', '-C', str(root), 'rev-parse', 'HEAD']).decode().strip(),
                'working_tree_dirty': bool(run(['git', '-C', str(root), 'status', '--porcelain']).strip()),
                'entries': entries, 'database': summary, 'runtime': runtime_manifest(home),
                'credentials': credentials, 'owner_uid': os.getuid(),
                'exclusions': ['credentials and login sessions', 'broker.lock', 'Codex account login', '.git and inventory',
                               'OS, SSH and Tailscale identity state', 'runtime binaries and venv', 'files outside source allowlist'],
                'restore_policy': 'Extract only into a new temporary/private directory. Never start Worker/main or services during restore test. Reconcile queued/running tasks and external side effects before actual production activation. Owner reprovisions credentials; do not auto-retry tasks.'}
    # Detect concurrent edits; never publish a mixed source snapshot silently.
    if source_files(root) != names or any((digest(regular(root / name)[0]), regular(root / name)[1]) != value for name, value in original.items()):
        raise ValueError('Source changed during snapshot; retry only after review')
    return payload, manifest


def write_bundle(folder, payload, manifest, budget=BUDGET):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    info = folder.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError('Backup directory must be owner-only')
    with tempfile.NamedTemporaryFile(dir=folder, prefix='.bundle-', delete=False) as stream:
        pending = Path(stream.name)
    try:
        with tarfile.open(pending, 'w:gz') as tf:
            files = dict(payload)
            files['manifest.json'] = (json.dumps(manifest, sort_keys=True, indent=2) + '\n').encode()
            for name, data in sorted(files.items()):
                member = tarfile.TarInfo(name)
                member.size = len(data)
                member.mode = manifest['entries'][name]['mode'] if name != 'manifest.json' else 0o600
                tf.addfile(member, io.BytesIO(data))
        size = pending.stat().st_size
        used = sum(p.stat().st_size for p in folder.iterdir() if p.is_file() and p != pending)
        if size > MAX_FILE or used + size + 65 > budget:
            raise ValueError('Recovery budget reached; old backups retained')
        name = 'recovery-' + time.strftime('%Y%m%d-%H%M%S', time.gmtime()) + '-' + str(time.time_ns()) + '.tar.gz'
        target = folder / name
        checksum = digest(pending.read_bytes())
        # Atomic publish without overwriting any existing snapshot.
        os.link(pending, target)
        fd = os.open(target.with_suffix('.sha256'), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as stream:
            stream.write(checksum + '\n')
        target.chmod(0o600); target.with_suffix('.sha256').chmod(0o600)
        return target
    finally:
        pending.unlink(missing_ok=True)


def validate_into(archive, destination):
    archive, destination = Path(archive), Path(destination)
    raw, _ = regular(archive, private=True)
    expected = regular(archive.with_suffix('.sha256'), private=True)[0].decode().strip()
    if digest(raw) != expected:
        raise ValueError('Checksum mismatch')
    # A caller-created new empty directory only; no production destination accepted.
    if destination.is_symlink() or not destination.is_dir() or any(destination.iterdir()):
        raise ValueError('Restore destination must be a new empty directory')
    destination.chmod(0o700)
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as tf:
        members = tf.getmembers(); names = set(); total = 0
        for m in members:
            p = PurePosixPath(m.name)
            if not m.isfile() or p.is_absolute() or '..' in p.parts or m.name != str(p) or m.name in names or m.mode not in (0o600, 0o700):
                raise ValueError('Unsafe/duplicate recovery member')
            if m.size > MAX_FILE:
                raise ValueError('Recovery member too large')
            names.add(m.name); total += m.size
        if total > MAX_EXPANDED or 'manifest.json' not in names:
            raise ValueError('Invalid recovery size/manifest')
        manifest = json.loads(tf.extractfile('manifest.json').read())
        entries = manifest['entries']
        if manifest['format'] != 1 or names != set(entries) | {'manifest.json'}:
            raise ValueError('Recovery file set mismatch')
        if not {'project/' + p for p in REQUIRED} <= names or 'data/tasks.sqlite3' not in names:
            raise ValueError('Incomplete application recovery')
        for m in members:
            data = tf.extractfile(m).read()
            if m.name != 'manifest.json':
                e = entries[m.name]
                if digest(data) != e['sha256'] or len(data) != e['size'] or m.mode != e['mode']:
                    raise ValueError('Recovery payload mismatch')
            path = destination / m.name
            directory = destination
            for part in PurePosixPath(m.name).parts[:-1]:
                directory = directory / part
                directory.mkdir(exist_ok=True, mode=0o700)
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(data)
            path.chmod(m.mode)
    path = destination / 'data/tasks.sqlite3'
    with contextlib.closing(sqlite3.connect(path.as_uri() + '?mode=ro&immutable=1', uri=True)) as db:
        summary = db_summary(db)
        if summary != manifest['database'] or summary['sessions'] != 0:
            raise ValueError('Recovered database differs from manifest')
    return manifest


def restore_test(archive):
    began = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='server5-recovery-test-') as temp:
        manifest = validate_into(archive, Path(temp))
        # Compile restored Python without importing application main or starting a worker.
        for path in (Path(temp) / 'project').rglob('*.py'):
            compile(path.read_bytes(), str(path), 'exec')
    return {'restore_test': 'passed', 'files': len(manifest['entries']),
            'tasks': manifest['database']['tasks']['count'], 'events': manifest['database']['events']['count'],
            'sessions': 0, 'seconds': round(time.monotonic() - began, 3),
            'production_data_touched': False, 'scope': 'source, units, safe settings, task/event data; credentials/runtime/OS require existing host or reprovisioning'}


def backup(root=None, home=None):
    if socket.gethostname() != 'server5':
        raise ValueError('Only server5')
    root = Path(root or Path(__file__).resolve().parents[1])
    home = Path(home or Path.home())
    folder = home / '.local/share/server5-commandcenter/backups'
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    info = folder.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError('Backup directory must be owner-only')
    fd = os.open(folder / '.recovery.lock', os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with tempfile.TemporaryDirectory(prefix='server5-backup-') as temp:
            payload, manifest = collect(root, home, Path(temp))
            target = write_bundle(folder, payload, manifest)
        result = restore_test(target)
    return {'archive': str(target), 'git_head': manifest['git_head'], 'working_tree_dirty': manifest['working_tree_dirty'],
            'tasks': result['tasks'], 'events': result['events'], 'restore_test': result['restore_test'],
            'credentials_archived': False}
