"""Transactional cancellation with one-time owner web confirmation; no signals."""
import contextlib
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
import time

SCHEMA = '''
CREATE TABLE IF NOT EXISTS cancel_confirmations(
 nonce_hash TEXT PRIMARY KEY, task_id TEXT NOT NULL, request_id TEXT NOT NULL,
 principal TEXT NOT NULL CHECK(principal='owner'), expires REAL NOT NULL);
CREATE TABLE IF NOT EXISTS cancel_receipts(
 request_id TEXT PRIMARY KEY, task_id TEXT NOT NULL, response TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS cancel_audit(
 seq INTEGER PRIMARY KEY, at REAL NOT NULL, request_id TEXT NOT NULL,
 task_id TEXT NOT NULL, principal TEXT NOT NULL, before_status TEXT NOT NULL,
 after_status TEXT NOT NULL, outcome TEXT NOT NULL);
'''
TERMINAL = {'succeeded','failed','cancelled','interrupted'}

class CancelError(ValueError):
    pass


def valid_id(value):
    return type(value) is str and re.fullmatch(r'[A-Za-z0-9_-]{16,80}', value)


def check_budget(db):
    # Fixed-size records and bounded rows; preserve all historical receipts/audit.
    if db.execute('SELECT count(*) FROM cancel_audit').fetchone()[0] >= 8000:
        raise CancelError('AUDIT_UNAVAILABLE')
    if db.execute('SELECT count(*) FROM cancel_confirmations').fetchone()[0] >= 8000:
        raise CancelError('AUDIT_UNAVAILABLE')


class Cancellation:
    def __init__(self, directory, clock=time.time):
        self.directory, self.clock = Path(directory), clock

    @contextlib.contextmanager
    def db(self):
        db = sqlite3.connect((self.directory/'tasks.sqlite3').as_uri()+'?mode=rw', uri=True, timeout=1)
        db.row_factory = sqlite3.Row
        try:
            with db:
                db.execute('BEGIN IMMEDIATE')
                yield db
        finally:
            db.close()

    def confirm(self, task_id, request_id, confirmed):
        if confirmed is not True or not valid_id(task_id) or not valid_id(request_id):
            raise CancelError('CONFIRMATION_REQUIRED')
        if os.path.lexists(self.directory/'mcp-cancel.disabled'):
            raise CancelError('DISABLED')
        nonce = secrets.token_urlsafe(32)
        with self.db() as db:
            check_budget(db)
            if not db.execute('SELECT 1 FROM tasks WHERE id=?',(task_id,)).fetchone():
                raise CancelError('NOT_FOUND')
            db.execute('INSERT INTO cancel_confirmations VALUES(?,?,?,?,?)',
                       (hashlib.sha256(nonce.encode()).hexdigest(),task_id,request_id,'owner',self.clock()+60))
        return dict(task_id=task_id,request_id=request_id,confirmation_id=nonce,expires_in_seconds=60)

    def cancel(self, task_id, request_id, confirmation_id, confirmed):
        if confirmed is not True:
            raise CancelError('CONFIRMATION_REQUIRED')
        if not valid_id(task_id) or not valid_id(request_id) or type(confirmation_id) is not str or not re.fullmatch(r'[A-Za-z0-9_-]{43,128}',confirmation_id):
            raise CancelError('INVALID_ARGUMENT')
        with self.db() as db:
            previous = db.execute('SELECT task_id,response FROM cancel_receipts WHERE request_id=?',(request_id,)).fetchone()
            if previous:
                if previous['task_id'] != task_id:
                    raise CancelError('REQUEST_CONFLICT')
                return json.loads(previous['response'])
            if os.path.lexists(self.directory/'mcp-cancel.disabled'):
                raise CancelError('DISABLED')
            check_budget(db)
            nonce_hash = hashlib.sha256(confirmation_id.encode()).hexdigest()
            proof = db.execute('SELECT * FROM cancel_confirmations WHERE nonce_hash=?',(nonce_hash,)).fetchone()
            if not proof or proof['principal'] != 'owner' or proof['task_id'] != task_id or proof['request_id'] != request_id or proof['expires'] < self.clock():
                raise CancelError('CONFIRMATION_REQUIRED')
            row = db.execute('SELECT status,cancel FROM tasks WHERE id=?',(task_id,)).fetchone()
            if not row:
                raise CancelError('NOT_FOUND')
            before = status = row['status']
            if status == 'queued':
                status, outcome = 'cancelled','queued_cancelled'
                db.execute("UPDATE tasks SET status='cancelled',cancel=1,finished=? WHERE id=?",(self.clock(),task_id))
            elif status == 'running':
                outcome = 'cancellation_requested'
                db.execute('UPDATE tasks SET cancel=1 WHERE id=?',(task_id,))
            elif status in TERMINAL:
                outcome = 'already_terminal'
            else:
                raise CancelError('UNAVAILABLE')
            result = dict(schema_version=1,task_id=task_id,request_id=request_id,outcome=outcome,status=status,
                          cancel_requested=bool(row['cancel']) or before in ('queued','running'),
                          stopped=status in TERMINAL and status != 'interrupted',effects_reverted=False)
            db.execute('DELETE FROM cancel_confirmations WHERE nonce_hash=?',(nonce_hash,))
            db.execute('INSERT INTO cancel_audit(at,request_id,task_id,principal,before_status,after_status,outcome) VALUES(?,?,?,?,?,?,?)',
                       (self.clock(),request_id,task_id,'owner',before,status,outcome))
            db.execute('INSERT INTO cancel_receipts VALUES(?,?,?)',(request_id,task_id,json.dumps(result,separators=(',',':'))))
            return result
