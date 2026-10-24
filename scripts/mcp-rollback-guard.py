#!/usr/bin/env python3
"""Independent, sandbox-only rollback guard. No production restore capability."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path.home() / '.local/state/server5-mcp-rollback-guard'
UNIT = 'server5-mcp-rollback-sandbox'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def write(path, data):
    tmp = path.with_suffix('.tmp')
    with open(tmp, 'wb') as out:
        os.fchmod(out.fileno(), 0o600)
        out.write(data)
        out.flush()
        os.fsync(out.fileno())
    os.replace(tmp, path)

def ctl(*args):
    return subprocess.run(['systemctl', '--user', *args], check=True,
                          capture_output=True, timeout=15)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'arm', 'restore', 'accept', 'disarm', 'status'])
    args = parser.parse_args()
    os.umask(0o077)
    ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
    if ROOT.is_symlink() or ROOT.stat().st_uid != os.getuid():
        raise RuntimeError('unsafe state root')
    with open(ROOT / 'lock', 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = ROOT / 'state.json'
        if args.action == 'prepare':
            if state.exists():
                print('already prepared; unchanged')
                return
            old, new = b'HEALTH_MAX_AGE_SECONDS = 180\n', b'HEALTH_MAX_AGE_SECONDS = 450\n'
            for name, data in [('previous', old), ('candidate', new), ('dummy', new)]:
                write(ROOT / name, data)
            write(state, json.dumps(dict(scope='sandbox-only', status='prepared', previous=digest(old), candidate=digest(new))).encode())
        else:
            s = json.loads(state.read_text())
            assert s['scope'] == 'sandbox-only'
            for name in ['previous', 'candidate']:
                assert digest((ROOT / name).read_bytes()) == s[name], 'backup hash mismatch'
            if args.action == 'arm':
                if s['status'] == 'armed':
                    print('already armed; deadline unchanged')
                    return
                assert s['status'] == 'prepared', 'prepare a fresh test directory for another arm'
                s.update(status='armed', deadline=time.time() + 180)
                write(state, json.dumps(s).encode())
                try:
                    subprocess.run(['systemd-run', '--user', '--quiet', '--unit='+UNIT,
                        '--on-active=180s', '--timer-property=AccuracySec=1s',
                        '--property=Type=oneshot', '--property=TimeoutStartSec=20s',
                        '--property=NoNewPrivileges=yes', '--property=ProtectSystem=strict',
                        '--property=ReadWritePaths='+str(ROOT), '--property=PrivateTmp=yes',
                        '/usr/bin/python3', str(Path(__file__).resolve()), 'restore'],
                        check=True, capture_output=True, timeout=15)
                except Exception:
                    s['status'] = 'disarmed'
                    write(state, json.dumps(s).encode())
                    raise
            elif args.action == 'restore':
                if s['status'] != 'armed':
                    print('no-op: not armed')
                    return
                assert time.time() >= s['deadline'], 'deadline not reached'
                assert digest((ROOT / 'dummy').read_bytes()) == s['candidate'], 'target changed; refuse overwrite'
                write(ROOT / 'dummy', (ROOT / 'previous').read_bytes())
                assert digest((ROOT / 'dummy').read_bytes()) == s['previous']
                s['status'] = 'restored'
                write(state, json.dumps(s).encode())
            elif args.action in ['accept', 'disarm']:
                # Persist decision under exclusive lock before stopping units.
                s['status'] = 'accepted' if args.action == 'accept' else 'disarmed'
                write(state, json.dumps(s).encode())
                if args.action == 'accept':
                    write(ROOT / 'ACCEPTED.json', json.dumps(dict(scope='sandbox-only', candidate=s['candidate'], accepted_at=time.time())).encode())
                for suffix in ['timer', 'service']:
                    # Missing/collected transient units are already disarmed.
                    p = subprocess.run(['systemctl', '--user', 'stop', UNIT+'.'+suffix], capture_output=True, timeout=15)
                    if p.returncode and b'not loaded' not in p.stderr:
                        raise RuntimeError('could not disarm sandbox unit')
            else:
                print(json.dumps(s, sort_keys=True))
                return
        print('OK sandbox-only:', args.action)

if __name__ == '__main__':
    main()
