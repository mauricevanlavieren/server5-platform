#!/usr/bin/env python3
"""Encrypt a reviewed local recovery bundle for later authorized off-host transfer.

No network transport, remote destination, keyring, credential lookup or timer.
Requires an owner-supplied public recipient file; never uses a private key.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile


def stage(archive, public_key, output):
    archive, public_key, output = map(Path, (archive, public_key, output))
    for path in (archive, public_key, archive.with_suffix('.sha256')):
        if path.is_symlink() or not path.is_file():
            raise ValueError('Regular explicit input files required')
        if any(p.is_symlink() for p in path.absolute().parents):
            raise ValueError('Symlink parent refused')
    if archive.stat().st_size > 256*1024**2 or public_key.stat().st_size > 1024*1024:
        raise ValueError('Input budget exceeded')
    expected = archive.with_suffix('.sha256').read_text().strip()
    if not re.fullmatch('[a-f0-9]{64}', expected):
        raise ValueError('Invalid checksum sidecar')
    with archive.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    if actual != expected:
        raise ValueError('Input checksum mismatch')
    output.mkdir(mode=0o700, parents=True, exist_ok=True)
    if output.is_symlink() or any(p.is_symlink() for p in output.absolute().parents):
        raise ValueError('Symlink output refused')
    info = output.stat()
    if info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError('Output must be owner-only')
    name = 'recovery-' + actual + '.gpg'
    final = output/name
    # An isolated home prevents reading the owner's private keyring/config.
    with tempfile.TemporaryDirectory(prefix='.encrypt-', dir=output) as temp:
        temp = Path(temp); temp.chmod(0o700)
        encrypted = temp/'bundle.gpg'
        subprocess.run(['/usr/bin/gpg', '--no-options', '--homedir', str(temp),
                        '--batch', '--no-tty', '--trust-model', 'always',
                        '--recipient-file', str(public_key.absolute()),
                        '--output', str(encrypted), '--encrypt', str(archive.absolute())],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90)
        encrypted.chmod(0o600)
        with encrypted.open('rb') as stream:
            cipher_hash = hashlib.file_digest(stream,'sha256').hexdigest()
            os.fsync(stream.fileno())
        # Atomic no-overwrite publication, no retention/deletion policy.
        os.link(encrypted, final)
    return dict(file=name, encrypted_sha256=cipher_hash, transfer_performed=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--recipient-public-key',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); os.umask(0o077)
    try:
        print(json.dumps(stage(a.archive,a.recipient_public_key,a.output)))
    except (ValueError,OSError,subprocess.SubprocessError):
        raise SystemExit('Staging refused/failed; no transfer performed')

if __name__=='__main__': main()
