#!/usr/bin/env python3
"""Explicit additive index preparation; no Store/recovery/worker lifecycle."""
import argparse
from pathlib import Path
import socket
import sqlite3
import time


def prepare(path):
    deadline = time.monotonic() + 3
    db = sqlite3.connect(Path(path).absolute().as_uri() + '?mode=rw', uri=True, timeout=1)
    try:
        db.set_progress_handler(lambda: int(time.monotonic() >= deadline), 500)
        with db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('CREATE INDEX IF NOT EXISTS mcp_tasks_created ON tasks(created DESC,id DESC)')
            db.execute('CREATE INDEX IF NOT EXISTS mcp_tasks_status_created ON tasks(status,created DESC,id DESC)')
    finally:
        db.close()


if __name__ == '__main__':
    if socket.gethostname() != 'server5':
        raise SystemExit('Only server5')
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', type=Path, default=Path.home() / '.local/state/server5-commandcenter/mvp/tasks.sqlite3')
    args = parser.parse_args()
    prepare(args.database)
    print('Additive MCP read-indexes prepared; no tasks changed.')
