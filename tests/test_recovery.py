import importlib.util
import io
from pathlib import Path
import tarfile
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('cc', Path(__file__).resolve().parents[1] / 'scripts/commandcenter.py')
cc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cc)


class RecoverySafetyTests(unittest.TestCase):
    def archive(self, name, kind=tarfile.REGTYPE):
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode='w') as tf:
            member = tarfile.TarInfo(name)
            member.type = kind
            if kind == tarfile.SYMTYPE:
                member.linkname = '/etc/passwd'
            tf.addfile(member)
        buffer.seek(0)
        return tarfile.open(fileobj=buffer)

    def test_path_traversal_rejected(self):
        for path in ['../outside', '/etc/passwd', 'docs/../../outside']:
            with self.subTest(path=path), self.archive(path) as tf:
                with self.assertRaises(ValueError):
                    cc.checked_members(tf)

    def test_symlink_and_device_rejected(self):
        for kind in [tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.CHRTYPE]:
            with self.subTest(kind=kind), self.archive('unsafe', kind) as tf:
                with self.assertRaises(ValueError):
                    cc.checked_members(tf)

    def test_regular_file_allowed(self):
        with self.archive('docs/safe.md') as tf:
            self.assertEqual(len(cc.checked_members(tf)), 1)

    def test_corruption_rejected_before_extract(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / ('a' * 40 + '.tar.gz')
            archive.write_bytes(b'corrupt')
            archive.with_suffix('.sha256').write_text('0' * 64)
            with self.assertRaisesRegex(ValueError, 'Checksum mismatch'):
                cc.restore_test(archive)


if __name__ == '__main__':
    unittest.main()
