#!/usr/bin/env python3
"""Prevent common credential files and literal keys from entering local commits."""
from pathlib import PurePosixPath
import re
import subprocess

paths = subprocess.check_output(['git', 'diff', '--cached', '--name-only', '--diff-filter=ACMR', '-z']).split(b'\0')
for raw in paths:
    if not raw:
        continue
    path = raw.decode()
    parts = PurePosixPath(path).parts
    name = parts[-1]
    if ('inventory' in parts or 'secrets' in parts or name in {'auth.json', 'credentials.json', 'id_rsa', 'id_ed25519'}
            or (name.startswith('.env') and name != '.env.example') or name.endswith(('.key', '.pem'))):
        raise SystemExit('Credential/inventory path rejected: ' + path)
    content = subprocess.check_output(['git', 'show', ':' + path])
    patterns = [rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
                rb'\bgh[pousr]_[A-Za-z0-9]{30,}', rb'\btskey-auth-[A-Za-z0-9-]{20,}',
                rb'\bsk-(?:proj-)?[A-Za-z0-9_-]{35,}']
    if any(re.search(pattern, content) for pattern in patterns):
        raise SystemExit('Possible literal credential rejected: ' + path)
print('Staged credential guard passed (heuristic; review still required).')
