#!/usr/bin/env python3
"""Read-only Server5 project entrypoint; no credentials, tasks or service changes."""
import os
from pathlib import Path
import socket
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def main():
    if socket.gethostname() != 'server5':
        print('mau is uitsluitend voor server5.', file=sys.stderr)
        return 1
    action = sys.argv[1:] or ['status']
    if len(action) != 1 or action[0] not in ('status', 'start', 'help', '--help'):
        print('Gebruik: mau [status|start|help]', file=sys.stderr)
        return 2
    if action[0] in ('help', '--help'):
        print('Gebruik: mau [status|start|help] — alleen lokale informatie lezen.')
        return 0
    if action[0] == 'status':
        env = dict(os.environ)
        runtime = Path('/run/user') / str(os.getuid())
        if (runtime / 'bus').exists():
            env['XDG_RUNTIME_DIR'] = str(runtime)
            env['DBUS_SESSION_BUS_ADDRESS'] = 'unix:path=' + str(runtime / 'bus')
        units = ['server5-commandcenter.service', 'server5-mcp.service',
                 'server5-mcp-tunnel.service', 'server5-health.timer',
                 'server5-backup.timer', 'server5-task-backup.timer']
        print('Server5 — actuele userdienststatus (geen end-to-end-bewijs):', flush=True)
        try:
            result = subprocess.run(['systemctl', '--user', 'show', *units,
                '-p', 'Id', '-p', 'ActiveState'], env=env, capture_output=True,
                text=True, timeout=5)
            print(result.stdout if result.returncode == 0 else 'Dienststatus niet beschikbaar.')
        except (OSError, subprocess.TimeoutExpired):
            print('Dienststatus niet beschikbaar.')
    name = 'START_HERE.md' if action[0] == 'start' else 'PROJECT_STATE.md'
    print((ROOT / 'docs' / name).read_text())
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
