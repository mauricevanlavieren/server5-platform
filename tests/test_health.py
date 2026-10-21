"""Healthy/unhealthy host fixtures only; no real service or resource failures."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import health
spec=importlib.util.spec_from_file_location('health_cc',Path(__file__).resolve().parents[1]/'scripts/commandcenter.py')
cc=importlib.util.module_from_spec(spec);spec.loader.exec_module(cc)


class HealthTests(unittest.TestCase):
    def observe(self,failed='',failed_code=0,ssh='active',listener='active',ntp='yes',ntp_code=0,
                mem=6*1024**3,free=80*1024**3,reboot=False):
        def command(args):
            if args[:2]==['systemctl','--failed']:return failed_code,failed
            if args[:2]==['systemctl','show']:
                state=ssh if args[2]=='ssh.service' else listener
                if state is None:return None,'unavailable'
                return 0,'LoadState=loaded\nActiveState='+state+'\nResult=success\n'
            return ntp_code,ntp
        with patch.object(health,'command',side_effect=command),patch.object(Path,'read_text',return_value='MemAvailable: '+str(mem//1024)+' kB\n'),patch.object(Path,'exists',return_value=reboot),patch.object(health.shutil,'disk_usage',return_value=SimpleNamespace(free=free)),patch.object(health.shutil,'which',return_value=None):
            return health.observe()
    def test_healthy(self):
        r=self.observe();self.assertEqual(r['status'],'ok');self.assertEqual(r['exit_code'],0)
    def test_fwupd_real_error_preserved(self):
        r=self.observe(failed='fwupd-refresh.service loaded failed failed Secret-free description\n')
        self.assertEqual(r['exit_code'],1)
        self.assertEqual(r['failed_units'],['fwupd-refresh.service'])
        self.assertIn('firmware_metadata_refresh_failed',r['errors'])
        self.assertNotIn('description',json.dumps(r))
    def test_unknown_system_failure_not_suppressed(self):
        r=self.observe(failed='important.service loaded failed failed Description\n')
        self.assertEqual(r['exit_code'],1);self.assertIn('system_unit_failed:important.service',r['errors'])
    def test_collector_failure_distinct(self):
        r=self.observe(failed='private subprocess stderr must not appear',failed_code=1)
        self.assertEqual(r['status'],'unknown');self.assertEqual(r['exit_code'],2)
        self.assertNotIn('private subprocess',json.dumps(r))
    def test_bad_systemctl_output_is_unknown(self):
        self.assertEqual(self.observe(failed='unexpected format')['exit_code'],2)
    def test_socket_activated_ssh_is_healthy(self):
        r=self.observe(ssh='inactive',listener='active');self.assertTrue(r['ssh_available']);self.assertEqual(r['exit_code'],0)
    def test_ssh_stopped(self):
        r=self.observe(ssh='inactive',listener='inactive');self.assertIn('ssh_not_active',r['errors']);self.assertEqual(r['exit_code'],1)
    def test_ssh_service_failed_even_with_socket(self):
        r=self.observe(ssh='failed');self.assertIn('ssh_unit_failed',r['errors']);self.assertFalse(r['ssh_available'])
    def test_unknown_ssh_without_active_path(self):
        self.assertEqual(self.observe(ssh=None,listener='inactive')['exit_code'],2)
    def test_resource_faults(self):
        r=self.observe(mem=100,free=100)
        self.assertEqual(r['exit_code'],1);self.assertEqual(len(r['errors']),2)
    def test_ntp_unsynchronized_and_unknown_differ(self):
        self.assertIn('ntp_not_synchronized',self.observe(ntp='no')['errors'])
        self.assertIn('ntp_measurement_unavailable',self.observe(ntp_code=None)['collector_errors'])
        self.assertEqual(self.observe(ntp='unexpected')['exit_code'],2)
    def test_reboot_notice_is_visible_not_outage(self):
        r=self.observe(reboot=True);self.assertEqual(r['status'],'warning');self.assertEqual(r['exit_code'],0)
        self.assertIn('reboot_required',r['warnings']);self.assertIn('reboot_required',r['alerts'])
    def test_optional_inventory_is_not_fault(self):
        r=self.observe();self.assertFalse(r['tools_present']['docker']);self.assertEqual(r['exit_code'],0)
    def test_measurement_timeout_never_leaks(self):
        with patch.object(health.subprocess,'run',side_effect=subprocess.TimeoutExpired('sensitive',3,stderr='private')):
            self.assertEqual(health.command(['synthetic']),(None,'timeout'))
        with patch.object(health.subprocess,'run',side_effect=OSError('private error')):
            self.assertEqual(health.command(['synthetic']),(None,'unavailable'))
    def test_missing_memory_does_not_crash(self):
        with patch.object(Path,'read_text',side_effect=OSError('private')):
            # Other observations can stay real only if mocked; avoid any actual command.
            with patch.object(health,'command',return_value=(None,'unavailable')),patch.object(health,'unit_state',return_value=None):
                r=health.observe()
        self.assertIn('memory_measurement_unavailable',r['collector_errors']);self.assertEqual(r['exit_code'],2)
    def test_unknown_does_not_erase_known_errors(self):
        r=self.observe(failed='fwupd-refresh.service loaded failed failed Metadata\n',ntp_code=None)
        self.assertEqual(r['exit_code'],2);self.assertIn('firmware_metadata_refresh_failed',r['alerts'])
    def test_record_latest_history_and_private_modes(self):
        with tempfile.TemporaryDirectory() as d:
            r=self.observe();health.record(r,d,cc.atomic)
            latest=Path(d)/'latest.json';hist=next(Path(d).glob('health-*.jsonl'))
            self.assertEqual(json.loads(latest.read_text()),json.loads(hist.read_text()))
            self.assertEqual(latest.stat().st_mode & 0o777,0o600);self.assertEqual(hist.stat().st_mode & 0o777,0o600)
    def test_history_limit_preserves_history_and_warns(self):
        import datetime
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/('health-'+datetime.date.today().isoformat()+'.jsonl')
            path.write_bytes(b'x'*(1024**2));r=health.record(self.observe(),d,cc.atomic)
            self.assertEqual(path.stat().st_size,1024**2);self.assertIn('history_budget_reached',r['warnings'])
            self.assertEqual(json.loads((Path(d)/'latest.json').read_text()),r)
    def test_history_symlink_refused_no_external_write(self):
        import datetime
        with tempfile.TemporaryDirectory() as d:
            dest=Path(d)/'keep';dest.write_text('unchanged')
            (Path(d)/('health-'+datetime.date.today().isoformat()+'.jsonl')).symlink_to(dest)
            r=health.record(self.observe(),d,cc.atomic)
            self.assertIn('history_write_failed',r['collector_errors']);self.assertEqual(dest.read_text(),'unchanged')
            self.assertEqual(r['exit_code'],2)
    def test_latest_write_failure_visible(self):
        with tempfile.TemporaryDirectory() as d:
            with patch.object(cc,'atomic',side_effect=PermissionError('private')):
                r=health.record(self.observe(),d,cc.atomic)
            self.assertEqual(r['exit_code'],2);self.assertIn('latest_write_failed',r['collector_errors'])


if __name__=='__main__':unittest.main()
