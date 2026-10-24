#!/usr/bin/env python3
"""Independent single-file release guard. Never restarts a service.

Production arming requires separate owner authorization. Preparation is inert.
State and target directories must be trusted, owner-controlled local directories.
"""
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import socket
import stat
import tempfile
import time

TARGET = Path('/home/mau/server5-commandcenter/web/mcp_reads.py')
STATE = Path('/home/mau/.local/state/server5-mcp-release-guard')
LIMIT = 1024 * 1024


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    # Reject symlink parents as well as symlink/nonregular leaves.
    path = Path(path).absolute()
    for parent in path.parents:
        if parent.is_symlink():
            raise ValueError('Symlink parent refused')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
            raise ValueError('Unsafe file')
        if info.st_mode & 0o022:
            raise ValueError('Writable by another user')
        data = stream.read(LIMIT + 1)
        if len(data) > LIMIT:
            raise ValueError('File limit exceeded')
        return data, stat.S_IMODE(info.st_mode)


def write(path, data, mode=0o600):
    fd, name = tempfile.mkstemp(prefix='.guard-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            os.fchmod(stream.fileno(), mode)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        dfd = os.open(path.parent, os.O_DIRECTORY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(name)


class Guard:
    def __init__(self, target=TARGET, state=STATE):
        self.target, self.root = Path(target), Path(state)

    @contextlib.contextmanager
    def locked(self):
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        for parent in (self.root, *self.root.parents):
            if parent.is_symlink():
                raise ValueError('Symlink state path refused')
        info = self.root.stat()
        if info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError('State must be owner-only')
        fd = os.open(self.root/'lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
        with os.fdopen(fd, 'r+') as lock:
            info = os.fstat(lock.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid():
                raise ValueError('Unsafe lock')
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield

    def save(self, s):
        write(self.root/'state.json', json.dumps(s, sort_keys=True).encode())

    def load(self):
        s = json.loads(read(self.root/'state.json')[0])
        if s['format'] != 1 or s['target'] != str(self.target):
            raise ValueError('Wrong release target')
        old, _ = read(self.root/'previous.py')
        if sha(old) != s['previous']:
            raise ValueError('Previous source hash mismatch')
        compile(old, '<previous>', 'exec')
        return s, old

    def prepare(self, previous):
        with self.locked():
            if (self.root/'state.json').exists():
                raise ValueError('Release already prepared; preserve evidence')
            old, _ = read(previous)
            candidate, mode = read(self.target)
            compile(old, '<previous>', 'exec'); compile(candidate, '<candidate>', 'exec')
            if old == candidate:
                raise ValueError('No release difference')
            write(self.root/'previous.py', old)
            write(self.root/'candidate.py', candidate)
            self.save(dict(format=1, target=str(self.target), status='prepared',
                           previous=sha(old), candidate=sha(candidate), mode=mode,
                           previous_mode=mode, prepared_at=time.time()))

    def transition(self, action, authorized=False, now=None):
        now = time.time() if now is None else now
        with self.locked():
            s, old = self.load()
            if action == 'arm':
                if not authorized:
                    raise ValueError('Separate explicit production authorization required')
                if s['status'] == 'armed':
                    return s
                if s['status'] != 'prepared':
                    raise ValueError('Terminal release cannot be rearmed')
                if sha(read(self.target)[0]) != s['candidate']:
                    raise ValueError('Target changed')
                s.update(status='armed', deadline=now+180)
            elif action == 'restore':
                if s['status'] != 'armed':
                    return s
                if now < s['deadline']:
                    raise ValueError('Deadline not reached')
                current, mode = read(self.target)
                # A crash after replace but before state persistence is recoverable.
                if sha(current) == s['previous']:
                    s['status'] = 'restored'
                elif sha(current) == s['candidate'] and mode == s['mode']:
                    write(self.target, old, s['previous_mode'])
                    if sha(read(self.target)[0]) != s['previous']:
                        raise ValueError('Restore verification failed')
                    s['status'] = 'restored'
                else:
                    raise ValueError('Target changed; refuse overwrite')
            elif action == 'accept':
                if s['status'] != 'armed' or now >= s['deadline']:
                    raise ValueError('Acceptance requires armed release before deadline')
                if sha(read(self.target)[0]) != s['candidate']:
                    raise ValueError('Target changed')
                s.update(status='accepted', accepted_at=now)
            elif action == 'disarm':
                if s['status'] in ('prepared', 'armed'):
                    s['status'] = 'disarmed'
            elif action != 'status':
                raise ValueError('Unknown action')
            self.save(s)
            return s


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'status', 'arm', 'restore', 'accept', 'disarm'])
    parser.add_argument('--previous', type=Path)
    parser.add_argument('--owner-authorized-production-arm', action='store_true')
    args = parser.parse_args()
    if socket.gethostname() != 'server5':
        raise SystemExit('Only server5')
    os.umask(0o077)
    guard = Guard()
    try:
        if args.action == 'prepare':
            if args.previous is None:
                parser.error('--previous is required')
            guard.prepare(args.previous)
            print('prepared; inactive; no timer or restart')
        else:
            s = guard.transition(args.action, authorized=args.owner_authorized_production_arm)
            print(json.dumps({k:s[k] for k in ['status','target','previous','candidate']}))
    except (ValueError, OSError, KeyError, SyntaxError):
        raise SystemExit('Guard refused operation; inspect local state without publishing contents')

if __name__ == '__main__':
    main()
