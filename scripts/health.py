"""Host health classification. No remediation, firmware, network or service writes."""
import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess


def command(args):
    """Only structured, bounded observations; never publish stderr or exceptions."""
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=3)
        return result.returncode, result.stdout
    except subprocess.TimeoutExpired:
        return None, 'timeout'
    except OSError:
        return None, 'unavailable'


def unit_state(unit):
    code, output = command(['systemctl', 'show', unit, '--property=LoadState,ActiveState,Result'])
    if code != 0:
        return None
    data = dict(line.split('=', 1) for line in output.splitlines() if '=' in line)
    if data.get('LoadState') != 'loaded' or data.get('ActiveState') not in {'active', 'inactive', 'failed', 'activating', 'deactivating'}:
        return None
    # Ignore arbitrary output; serialize only normalized status values.
    return {'state': data['ActiveState'], 'result': 'success' if data.get('Result') == 'success' else 'non-success'}


def classify(result):
    result['status'] = ('unknown' if result['collector_errors'] else
                        'error' if result['errors'] else 'warning' if result['warnings'] else 'ok')
    result['exit_code'] = 2 if result['collector_errors'] else 1 if result['errors'] else 0
    # Compatibility field still includes every issue; no consumer should silently lose an alert.
    result['alerts'] = result['errors'] + result['collector_errors'] + result['warnings']
    return result


def observe():
    result = {'schema_version': 2, 'utc': dt.datetime.now(dt.timezone.utc).isoformat(),
              'hostname': socket.gethostname(), 'errors': [], 'warnings': [], 'collector_errors': [],
              'failed_units': [], 'reboot_required': Path('/var/run/reboot-required').exists(),
              'tools_present': {x: bool(shutil.which(x)) for x in ['bwrap', 'tailscale', 'docker']}}
    try:
        mem = dict((name, int(value.split()[0]) * 1024)
                   for line in Path('/proc/meminfo').read_text().splitlines()
                   for name, value in [line.split(':', 1)])
        result['memory_available_bytes'] = mem['MemAvailable']
        if mem['MemAvailable'] < 2 * 1024**3:
            result['errors'].append('available_memory_below_2GiB')
    except (OSError, ValueError, KeyError):
        result['memory_available_bytes'] = None
        result['collector_errors'].append('memory_measurement_unavailable')
    try:
        result['root_free_bytes'] = shutil.disk_usage('/').free
        if result['root_free_bytes'] < 15 * 1024**3:
            result['errors'].append('root_free_below_15GiB')
    except OSError:
        result['root_free_bytes'] = None
        result['collector_errors'].append('disk_measurement_unavailable')
    try:
        result['load'] = list(os.getloadavg())
    except OSError:
        result['load'] = None
        result['collector_errors'].append('load_measurement_unavailable')
    code, output = command(['systemctl', '--failed', '--no-legend', '--plain', '--no-pager'])
    if code != 0:
        result['collector_errors'].append('system_units_measurement_unavailable')
    else:
        for line in output.splitlines():
            fields = line.split()
            if not fields:
                continue
            if len(fields) < 4 or fields[2:4] != ['failed', 'failed'] or not re.fullmatch(r'[A-Za-z0-9_.@:\\-]+', fields[0]):
                result['collector_errors'].append('system_units_output_invalid')
                break
            result['failed_units'].append(fields[0])
        # A failed maintenance job is a real error, not "no updates" or a healthy host.
        for unit in result['failed_units']:
            result['errors'].append('firmware_metadata_refresh_failed' if unit == 'fwupd-refresh.service' else 'system_unit_failed:' + unit)
    service, listener = unit_state('ssh.service'), unit_state('ssh.socket')
    result['ssh_active'] = service['state'] if service else 'unknown'
    result['ssh_socket_active'] = listener['state'] if listener else 'unknown'
    if (service and service['state'] == 'failed') or (listener and listener['state'] == 'failed'):
        result['errors'].append('ssh_unit_failed')
    elif (service and service['state'] == 'active') or (listener and listener['state'] == 'active'):
        # A loaded but inactive service with a healthy listening socket is valid socket activation.
        result['ssh_available'] = True
    elif service is None or listener is None:
        result['collector_errors'].append('ssh_measurement_unavailable')
    else:
        result['errors'].append('ssh_not_active')
    result.setdefault('ssh_available', False)
    code, output = command(['timedatectl', 'show', '-p', 'NTPSynchronized', '--value'])
    state = output.strip()
    result['ntp_synchronized'] = state if code == 0 and state in {'yes', 'no'} else 'unknown'
    if result['ntp_synchronized'] == 'unknown':
        result['collector_errors'].append('ntp_measurement_unavailable')
    elif state == 'no':
        result['errors'].append('ntp_not_synchronized')
    if result['reboot_required']:
        result['warnings'].append('reboot_required')
    # Missing optional tools are inventory, not a host outage. Do not probe their runtimes.
    return classify(result)


def record(result, state, atomic):
    state = Path(state)
    history = state / ('health-' + dt.date.today().isoformat() + '.jsonl')
    payload = (json.dumps(result, sort_keys=True) + '\n').encode()
    try:
        total = sum(p.stat().st_size for p in state.glob('health-*.jsonl'))
        full = total + len(payload) > 128 * 1024**2 or (history.exists() and history.stat().st_size + len(payload) > 1024**2)
    except OSError:
        full = True
        result['collector_errors'].append('history_measurement_unavailable')
        classify(result)
    if full and 'history_measurement_unavailable' not in result['collector_errors']:
        result['warnings'].append('history_budget_reached')
        classify(result)
    try:
        atomic(state / 'latest.json', (json.dumps(result, sort_keys=True) + '\n').encode())
    except OSError:
        result['collector_errors'].append('latest_write_failed')
        return classify(result)
    if not full:
        try:
            # Open without following a symlink and with private permissions from creation.
            fd = os.open(history, os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, 'ab') as stream:
                os.fchmod(stream.fileno(), 0o600)
                stream.write((json.dumps(result, sort_keys=True) + '\n').encode())
        except OSError:
            result['collector_errors'].append('history_write_failed')
            classify(result)
            try:
                atomic(state / 'latest.json', (json.dumps(result, sort_keys=True) + '\n').encode())
            except OSError:
                result['collector_errors'].append('latest_write_failed')
                classify(result)
    return result
