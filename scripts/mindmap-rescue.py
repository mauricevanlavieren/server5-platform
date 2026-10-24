#!/usr/bin/env python3
"""Owner-only Server5 outbox rescue, independent of HTTP/worker queue.
Never executes tasks, reads credentials, or restarts services.
"""
import argparse
import fcntl
from pathlib import Path
import socket
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'web'))
from commandcenter import Store, STATE


def main():
    if socket.gethostname() != 'server5':
        raise SystemExit('Server5 only')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['status', 'drain', 'rearm'])
    parser.add_argument('--seq', type=int)
    args = parser.parse_args()
    store = Store(STATE)
    if args.action == 'rearm':
        if args.seq is None:
            parser.error('rearm requires --seq (one explicit event)')
        with (STATE / 'mindmap-dispatch.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with store.db() as db:
                db.execute('DELETE FROM mindmap_retry WHERE seq=? AND EXISTS (SELECT 1 FROM mindmap_outbox WHERE seq=? AND delivered=0)', (args.seq, args.seq))
    elif args.action == 'drain':
        print('delivered:', store.drain_mindmap())
    with store.db() as db:
        print('task status counts:', [tuple(r) for r in db.execute('SELECT status,count(*) FROM tasks GROUP BY status')])
        print('recent task metadata:', [tuple(r) for r in db.execute('SELECT id,status,exit_code FROM tasks ORDER BY created DESC LIMIT 5')])
        print('outbox:', [tuple(r) for r in db.execute('SELECT delivered,count(*) FROM mindmap_outbox GROUP BY delivered')])
        print('pending metadata:', [tuple(r) for r in db.execute('SELECT o.seq,o.task_id,o.status,coalesce(r.attempts,0),r.error_type FROM mindmap_outbox o LEFT JOIN mindmap_retry r USING(seq) WHERE o.delivered=0 ORDER BY seq LIMIT 20')])

if __name__ == '__main__':
    main()
