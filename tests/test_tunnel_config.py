import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('tunnel_setup', Path(__file__).resolve().parents[1] / 'scripts/configure-tunnel.py')
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class TunnelProvisionTests(unittest.TestCase):
    def provision(self, home, inputs, key='sk-' + 'A' * 40):
        out = io.StringIO()
        with patch.object(setup.socket, 'gethostname', return_value='server5'), \
                patch.object(setup.sys.stdin, 'isatty', return_value=True), \
                patch.object(setup.Path, 'home', return_value=Path(home)), \
                patch('builtins.input', side_effect=inputs), \
                patch.object(setup.getpass, 'getpass', return_value=key), \
                contextlib.redirect_stdout(out):
            setup.main()
        return out.getvalue()

    def test_private_files_and_no_key_in_profile_or_output(self):
        with tempfile.TemporaryDirectory() as home:
            key = 'sk-' + 'A' * 40
            out = self.provision(home, ['tunnel_' + 'a' * 32, 'ja'], key)
            directory = Path(home) / '.config/server5-commandcenter'
            self.assertEqual((directory / 'tunnel-runtime-key').stat().st_mode & 0o777, 0o600)
            self.assertEqual((directory / 'tunnel.yaml').stat().st_mode & 0o777, 0o600)
            self.assertNotIn(key, out)
            self.assertNotIn(key, (directory / 'tunnel.yaml').read_text())

    def test_existing_key_preserved(self):
        with tempfile.TemporaryDirectory() as home:
            self.provision(home, ['tunnel_' + 'a' * 32, 'ja'])
            p = Path(home) / '.config/server5-commandcenter/tunnel-runtime-key'
            before = p.read_bytes()
            with self.assertRaises(SystemExit): self.provision(home, [])
            self.assertEqual(p.read_bytes(), before)

    def test_invalid_id_creates_no_key(self):
        with tempfile.TemporaryDirectory() as home:
            with self.assertRaises(SystemExit): self.provision(home, ['nieuwe tunnel'])
            self.assertFalse((Path(home) / '.config/server5-commandcenter/tunnel-runtime-key').exists())

    def test_unconfirmed_restricted_rights_create_no_key(self):
        with tempfile.TemporaryDirectory() as home:
            with self.assertRaises(SystemExit): self.provision(home, ['tunnel_' + 'a' * 32, 'nee'])
            self.assertFalse((Path(home) / '.config/server5-commandcenter/tunnel-runtime-key').exists())
