"""Private durable decision channel, independent of queue and publication locks."""
import argparse
import contextlib
import json
import os
from pathlib import Path
import re
import sqlite3
import time

STATE = Path.home()/'.local/state/server5-commandcenter/mvp'

class Decisions:
    def __init__(self, directory=STATE):
        self.directory = Path(directory)
        self.path = self.directory/'decisions.sqlite3'
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        with self.db() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS decisions(
                id TEXT PRIMARY KEY, task_id TEXT NOT NULL, question TEXT NOT NULL,
                options TEXT NOT NULL, context TEXT NOT NULL, requires_owner INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending', created REAL NOT NULL,
                answered REAL, answer TEXT, answer_id TEXT UNIQUE, owner_confirmed INTEGER)''')
        self.path.chmod(0o600)

    @contextlib.contextmanager
    def db(self):
        db = sqlite3.connect(self.path, timeout=3)
        db.row_factory = sqlite3.Row
        try:
            db.execute('PRAGMA synchronous=FULL')
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def key(value):
        if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_-]{16,80}', value):
            raise ValueError('ID must contain 16–80 safe characters')
        return value

    @staticmethod
    def text(value, limit):
        if not isinstance(value, str) or not value.strip() or len(value)>limit:
            raise ValueError('Missing or oversized text')
        from commandcenter import redact
        if redact(value) != value:
            raise ValueError('Credentials prohibited')
        return value

    def ask(self, request_id, task_id, question, options, context='', requires_owner=False):
        self.key(request_id); self.key(task_id)
        self.text(question, 2000)
        if not isinstance(options, list) or len(options)>8:
            raise ValueError('At most eight options')
        for option in options: self.text(option, 500)
        if context: self.text(context, 4000)
        payload=(task_id,question,json.dumps(options),context,int(requires_owner))
        # Only inspect metadata, never task prompt/result/credentials.
        with sqlite3.connect((self.directory/'tasks.sqlite3').as_uri()+'?mode=ro',uri=True,timeout=3) as tasks:
            task=tasks.execute('SELECT status,cancel FROM tasks WHERE id=?',(task_id,)).fetchone()
        if not task or task[0]!='running' or task[1]:
            raise ValueError('Task must be running and not cancelled')
        with self.db() as db:
            db.execute('INSERT OR IGNORE INTO decisions(id,task_id,question,options,context,requires_owner,created) VALUES(?,?,?,?,?,?,?)',(request_id,*payload,time.time()))
            row=db.execute('SELECT * FROM decisions WHERE id=?',(request_id,)).fetchone()
            if tuple(row[k] for k in ('task_id','question','options','context','requires_owner')) != payload:
                raise ValueError('Request ID conflict')
        return self.get(request_id)

    def get(self, request_id):
        self.key(request_id)
        with self.db() as db: row=db.execute('SELECT * FROM decisions WHERE id=?',(request_id,)).fetchone()
        if row is None: raise ValueError('Unknown decision')
        result=dict(row);result['options']=json.loads(result['options'])
        return result

    def pending(self):
        with self.db() as db:
            return [dict(r) | {'options':json.loads(r['options'])} for r in db.execute("SELECT * FROM decisions WHERE status='pending' ORDER BY created LIMIT 25")]

    def answer(self, request_id, answer_id, answer, owner_confirmed=False):
        self.key(request_id);self.key(answer_id);self.text(answer,4000)
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT * FROM decisions WHERE id=?',(request_id,)).fetchone()
            if row is None: raise ValueError('Unknown decision')
            if row['status']=='answered':
                if (row['answer_id'],row['answer'],row['owner_confirmed']) != (answer_id,answer,int(owner_confirmed)):
                    raise ValueError('Answer conflict')
            else:
                if row['requires_owner'] and not owner_confirmed:
                    raise ValueError('Explicit owner approval required')
                db.execute("UPDATE decisions SET status='answered',answer=?,answer_id=?,owner_confirmed=?,answered=? WHERE id=?",(answer,answer_id,int(owner_confirmed),time.time(),request_id))
        return self.get(request_id)

    def wait(self, request_id, timeout=60, interval=1):
        if not 0<=timeout<=600 or not 0.05<=interval<=5: raise ValueError('Invalid wait bounds')
        deadline=time.monotonic()+timeout
        while True:
            row=self.get(request_id)
            with sqlite3.connect((self.directory/'tasks.sqlite3').as_uri()+'?mode=ro',uri=True,timeout=3) as db:
                task=db.execute('SELECT status,cancel FROM tasks WHERE id=?',(row['task_id'],)).fetchone()
            if not task or task[0]!='running' or task[1]:
                raise ValueError('Task stopped; reconcile explicitly, never replay')
            if row['status']=='answered' or time.monotonic()>=deadline: return row
            time.sleep(min(interval,max(0,deadline-time.monotonic())))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--state',type=Path,default=Path(os.environ.get('SERVER5_DECISION_STATE',STATE)))
    s=p.add_subparsers(dest='action',required=True)
    a=s.add_parser('ask');a.add_argument('id');a.add_argument('question');a.add_argument('--task-id',default=os.environ.get('SERVER5_TASK_ID'));a.add_argument('--options',type=json.loads,default=[]);a.add_argument('--context',default='');a.add_argument('--requires-owner',action='store_true')
    w=s.add_parser('wait');w.add_argument('id');w.add_argument('--timeout',type=float,default=60)
    args=p.parse_args();d=Decisions(args.state)
    row=d.ask(args.id,args.task_id,args.question,args.options,args.context,args.requires_owner) if args.action=='ask' else d.wait(args.id,args.timeout)
    print(json.dumps(row,ensure_ascii=False))
    if args.action=='wait' and row['status']=='pending': raise SystemExit(2)

if __name__=='__main__': main()
