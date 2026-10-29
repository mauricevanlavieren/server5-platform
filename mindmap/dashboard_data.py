"""Local, credential-free dashboard projection; no task prompts or results."""
from pathlib import Path
from datetime import datetime, timezone
import os
import shutil
import sqlite3
import subprocess
import socket
import concurrent.futures
import shlex
import time


def dashboard_status():
    now = datetime.now(timezone.utc).isoformat()
    result = {'hostname': 'server5', 'observed_at': now, 'stale': False,
              'sources': {'host': '/proc, statvfs', 'tasks': 'existing broker SQLite (read-only)'},
              'load': list(os.getloadavg()), 'cpu_count': os.cpu_count(),
              'cpu_percent': None, 'uptime_seconds': None,
              'memory_available_bytes': None, 'memory_total_bytes': None,
              'root_free_bytes': None, 'root_total_bytes': None}
    try:
        result['uptime_seconds'] = float(Path('/proc/uptime').read_text().split()[0])
        mem = {line.split(':')[0]: int(line.split()[1])*1024
               for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith(('MemTotal:', 'MemAvailable:'))}
        result.update(memory_available_bytes=mem['MemAvailable'], memory_total_bytes=mem['MemTotal'])
        disk = shutil.disk_usage('/')
        result.update(root_free_bytes=disk.free, root_total_bytes=disk.total)
    except (OSError, ValueError, KeyError):
        result['stale'] = True
    result['services'] = {}
    env = dict(os.environ, XDG_RUNTIME_DIR=f'/run/user/{os.getuid()}',
               DBUS_SESSION_BUS_ADDRESS=f'unix:path=/run/user/{os.getuid()}/bus')
    units = ('server5-commandcenter.service', 'server5-mindmap.service',
             'server5-mcp.service', 'server5-health.timer', 'server5-backup.timer',
             'server5-task-backup.timer')
    try:
        probe = subprocess.run(['systemctl', '--user', 'show', *units,
                                '--property=Id,ActiveState', '--no-pager'],
                               capture_output=True, text=True, timeout=3, env=env)
        for record in probe.stdout.strip().split('\n\n'):
            fields = dict(line.split('=', 1) for line in record.splitlines() if '=' in line)
            if fields.get('Id') in units:
                result['services'][fields['Id']] = fields.get('ActiveState', 'unknown')
    except (OSError, subprocess.TimeoutExpired):
        pass
    for unit in units:
        result['services'].setdefault(unit, 'unknown')
    result['queue'] = {'available': False, 'counts': {}, 'recent': []}
    result['projects'] = {'available': False, 'items': []}
    database = Path.home()/'.local/state/server5-commandcenter/mvp/tasks.sqlite3'
    try:
        with sqlite3.connect(database.as_uri()+'?mode=ro', uri=True, timeout=1) as db:
            db.execute('PRAGMA query_only=ON')
            counts = dict(db.execute('SELECT status,count(*) FROM tasks GROUP BY status'))
            recent = [dict(zip(('id','status','created','finished'), row)) for row in db.execute(
                "SELECT id,status,created,finished FROM tasks ORDER BY CASE status WHEN 'running' THEN 0 WHEN 'queued' THEN 1 ELSE 2 END,created DESC LIMIT 8")]
            result['queue'] = {'available': True, 'counts': counts, 'recent': recent}
            items = [dict(zip(('id','status','stages','max_stages'), row)) for row in db.execute(
                'SELECT id,status,stages,max_stages FROM project_goals ORDER BY deadline DESC LIMIT 8')]
            result['projects'] = {'available': True, 'items': items}
    except (OSError, sqlite3.Error):
        pass
    result['network_center'] = network_center()
    return result


def network_center():
    """Project existing local reports only; never contact the listed hosts."""
    import re
    root = Path(__file__).resolve().parents[1]
    reports = ('docs/ssh-servers12-2026-10-23.md',
               'docs/ssh-server3-2026-10-23.md',
               'docs/ssh-servers46-2026-10-23.md')
    hosts = {}
    for source in reports:
        try:
            text = (root / source).read_text()
        except OSError:
            continue
        pairs = re.findall(r'(server[1-6]) / (192\.168\.1\.\d+)', text)
        if source.endswith('ssh-server3-2026-10-23.md'):
            pairs += [('server3', ip) for ip in re.findall(r'Netwerk-hostkey ED25519 van (192\.168\.1\.\d+)', text)]
        for hostname, address in pairs:
            hosts[(hostname, address)] = {
                'hostname': hostname, 'ip': address, 'reachability': 'unknown',
                'measured_at': None, 'source': source,
                'historical': 'SSH-antwoord vastgelegd op 2026-10-23; verouderde waarneming, exacte meettijd/tijdzone onbekend'}
    hosts[('server5', '192.168.1.245')] = {
        'hostname': 'server5', 'ip': '192.168.1.245', 'reachability': 'unknown',
        'measured_at': None, 'source': 'mindmap/serve.py (bestaand bindadres)',
        'historical': 'Bekende lokale configuratie; geen bereikbaarheidsmeting'}
    return sorted(hosts.values(), key=lambda host: (host['hostname'], host['ip']))


FLEET = {
    'server1': ('192.168.1.201', None),
    'server2': ('192.168.1.138', None),
    'server3': ('192.168.1.224', None),
    'server4': ('192.168.1.163', 'server4'),
    'server5': ('192.168.1.245', None),
    'server6': ('192.168.1.15', '192.168.1.175'),
}

REMOTE_METRICS = (
    "import time,json,shutil; "
    "r=lambda: tuple(map(int,open('/proc/stat').readline().split()[1:8])); "
    "a=r(); time.sleep(.25); b=r(); "
    "total=sum(b)-sum(a); idle=(b[3]+b[4])-(a[3]+a[4]); "
    "m={x.split(':')[0]:int(x.split()[1])*1024 for x in open('/proc/meminfo') if x.startswith(('MemTotal:','MemAvailable:'))}; "
    "d=shutil.disk_usage('/'); "
    "print(json.dumps({'cpu_percent':round(100*(total-idle)/total,1) if total else None,'ram_percent':round(100*(m['MemTotal']-m['MemAvailable'])/m['MemTotal'],1),'disk_percent':round(100*(d.total-d.free)/d.total,1)}))"
)


def _local_metrics():
    def cpu():
        return tuple(map(int, Path('/proc/stat').read_text().splitlines()[0].split()[1:8]))
    try:
        first = cpu()
        time.sleep(.25)
        second = cpu()
        total = sum(second) - sum(first)
        idle = second[3] + second[4] - first[3] - first[4]
        mem = {line.split(':')[0]: int(line.split()[1]) * 1024
               for line in Path('/proc/meminfo').read_text().splitlines()
               if line.startswith(('MemTotal:', 'MemAvailable:'))}
        disk = shutil.disk_usage('/')
        return {'cpu_percent': round(100 * (total - idle) / total, 1) if total else None,
                'ram_percent': round(100 * (mem['MemTotal'] - mem['MemAvailable']) / mem['MemTotal'], 1),
                'disk_percent': round(100 * (disk.total - disk.free) / disk.total, 1)}
    except (OSError, ValueError, KeyError, ZeroDivisionError):
        return None


def _fleet_host(item):
    name, (ip, host_key_alias) = item
    measured = datetime.now(timezone.utc).isoformat()
    if name == 'server5':
        metrics = _local_metrics()
        return {'name': name, 'ip': ip, 'status': 'online', 'metrics': metrics,
                'measured_at': measured, 'source': 'lokale /proc en statvfs'}
    try:
        with socket.create_connection((ip, 22), timeout=1.2):
            status = 'online'
    except ConnectionRefusedError:
        return {'name': name, 'ip': ip, 'status': 'offline', 'metrics': None,
                'measured_at': measured, 'source': 'SSH-poort geweigerd'}
    except OSError:
        return {'name': name, 'ip': ip, 'status': 'unknown', 'metrics': None,
                'measured_at': measured, 'source': 'SSH-bereikbaarheid niet vastgesteld'}
    options = ['ssh', '-F', '/dev/null', '-i', '/home/mau/.ssh/id_ed25519_server5_servers12',
               '-o', 'IdentitiesOnly=yes', '-o', 'IdentityAgent=none',
               '-o', 'StrictHostKeyChecking=yes', '-o', 'BatchMode=yes',
               '-o', 'ConnectTimeout=2', '-o', 'ConnectionAttempts=1']
    if host_key_alias:
        options += ['-o', 'HostKeyAlias=' + host_key_alias]
    options += ['mau@' + ip, 'python3 -c ' + shlex.quote(REMOTE_METRICS)]
    try:
        probe = subprocess.run(options, capture_output=True, text=True, timeout=4)
        if probe.returncode == 0:
            import json
            metrics = json.loads(probe.stdout)
            if not all(isinstance(metrics.get(key), (int, float)) for key in
                       ('cpu_percent', 'ram_percent', 'disk_percent')):
                raise ValueError('invalid metrics')
            return {'name': name, 'ip': ip, 'status': status, 'metrics': metrics,
                    'measured_at': datetime.now(timezone.utc).isoformat(), 'source': 'SSH read-only'}
    except (OSError, subprocess.TimeoutExpired, ValueError):
        pass
    return {'name': name, 'ip': ip, 'status': status, 'metrics': None,
            'measured_at': measured, 'source': 'host bereikbaar; actuele metrics niet beschikbaar'}


def fleet_status():
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        hosts = list(pool.map(_fleet_host, FLEET.items()))
    return {'observed_at': datetime.now(timezone.utc).isoformat(), 'hosts': hosts}
