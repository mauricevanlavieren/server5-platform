#!/usr/bin/env python3
"""Emit reviewed Git Markdown for explicit connector publication; no network or auth."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
def git(*args):
    return subprocess.check_output(['git', '-C', str(root), *args])

if git('status', '--porcelain').strip():
    sys.exit('Commit reviewed changes before export')
commit = git('rev-parse', 'HEAD').decode().strip()
paths = git('ls-tree', '-r', '--name-only', '-z', 'HEAD').split(b'\0')
files = []
for raw in paths:
    if raw and raw.endswith(b'.md'):
        path = raw.decode()
        if not (path in {'README.md', 'AGENTS.md'} or path.startswith(('docs/', 'plans/', 'templates/'))):
            continue
        data = git('show', 'HEAD:' + path)
        files.append({'path': path, 'sha256': hashlib.sha256(data).hexdigest(), 'content': data.decode()})
print(json.dumps({'commit': commit, 'scope': 'reviewed Git Markdown only', 'files': files}, ensure_ascii=False))
