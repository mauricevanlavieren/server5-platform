"""Bounded owner-only read capabilities. No worker, raw log or host probes."""
import base64
import contextlib
import datetime as dt
import fcntl
import hashlib
import hmac
import json
import math
import os
from pathlib import Path
import secrets
import sqlite3
import stat
import threading
import time
from typing import Annotated, Literal

import anyio
from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult, TextContent, Tool, ToolAnnotations
from pydantic import BaseModel, ConfigDict, Field

# Collector: 300s cadence + 15s jitter + 60s accuracy + 45s timeout;
# retain 30s scheduling margin. Re-evaluate if the health timer changes.
HEALTH_MAX_AGE_SECONDS = 450

Status = Literal['queued', 'running', 'succeeded', 'failed', 'cancelled', 'interrupted']
ID = Annotated[str, Field(min_length=16, max_length=80, pattern=r'^[A-Za-z0-9_-]{16,80}$')]
Cursor = Annotated[str, Field(min_length=1, max_length=512, pattern=r'^[A-Za-z0-9_-]+$')]
Limit = Annotated[int, Field(ge=1, le=50)]
Date = Annotated[str, Field(pattern=r'^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z$', json_schema_extra={'format': 'date-time'})]


class Model(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid', allow_inf_nan=False)


class ListInput(Model):
    limit: Limit = 20
    status: Status = Field(default=None)  # Optional presence, never JSON null.
    cursor: Cursor = Field(default=None)


class LogsInput(Model):
    task_id: ID
    limit: Limit = 20
    cursor: Cursor = Field(default=None)


class HealthInput(Model):
    pass


class Meta(Model):
    id: ID
    status: Status
    created: Date
    started: Date | None
    finished: Date | None
    exit_code: int | None
    cancel: bool


class ListOutput(Model):
    schema_version: Literal[1]
    items: Annotated[list[Meta], Field(max_length=50)]
    next_cursor: Cursor | None
    snapshot_at: Date


Kinds = Literal['worker_started', 'turn_completed', 'turn_failed', 'cancellation_requested', 'execution_event', 'details_withheld']
Messages = Literal['Worker gestart.', 'Uitvoering afgerond.', 'Uitvoering mislukt.', 'Annulering aangevraagd.', 'Uitvoeringsgebeurtenis.', 'Details afgeschermd.']
LABELS = dict(zip(Kinds.__args__, Messages.__args__))


class Entry(Model):
    seq: Annotated[int, Field(ge=1, le=9223372036854775807)]
    at: Date
    kind: Kinds
    message: Messages


class LogsOutput(Model):
    schema_version: Literal[1]
    task_id: ID
    entries: Annotated[list[Entry], Field(max_length=50)]
    next_cursor: Cursor | None
    snapshot_complete: bool
    details_withheld: bool


Issues = Literal['firmware_metadata_refresh_failed', 'low_memory', 'low_disk', 'reboot_required', 'ssh_unavailable', 'ntp_unsynchronized', 'other_system_failure', 'collector_unavailable', 'snapshot_stale']
Bytes = Annotated[int, Field(ge=0)]


class HealthOutput(Model):
    schema_version: Literal[1]
    host: Literal['server5']
    observed_at: Date | None
    stale: bool
    status: Literal['ok', 'warning', 'error', 'unknown']
    memory_available_bytes: Bytes | None
    root_free_bytes: Bytes | None
    load: Annotated[list[Annotated[float, Field(ge=0)]], Field(min_length=3, max_length=3)] | None
    reboot_required: bool | None
    ssh_available: bool | None
    ntp_synchronized: Literal['yes', 'no', 'unknown']
    issues: Annotated[list[Issues], Field(max_length=16)]


INPUTS = {'list_tasks': ListInput, 'task_logs': LogsInput, 'server_health': HealthInput}
OUTPUTS = {'list_tasks': ListOutput, 'task_logs': LogsOutput, 'server_health': HealthOutput}
DESCRIPTIONS = {
    'list_tasks': 'Lees uitsluitend taakmetadata in begrensde pagina’s. Statuswaarden zijn actueel; de insertion-snapshot is geen historische statusfeed.',
    'task_logs': 'Lees uitsluitend vaste veilige eventlabels. Geen raw logs of vrije tekst. Snapshotvoltooiing betekent geen taakvoltooiing.',
    'server_health': 'Lees de bestaande hostmeting met timestamp/staleness; geen actieve probe, workerheartbeat of herstelactie.',
}


def schema(model):
    result = model.model_json_schema()
    result['$schema'] = 'https://json-schema.org/draft/2020-12/schema'
    # Omitted optional inputs have defaults internally, but null is not legal.
    for value in result.get('properties', {}).values():
        if value.get('default', 'absent') is None:
            del value['default']
    return result


class ReadError(Exception):
    def __init__(self, code, retry=None):
        self.code, self.retry = code, retry


def utc(value):
    if type(value) not in (float, int) or not math.isfinite(value):
        raise ReadError('UNAVAILABLE')
    return dt.datetime.fromtimestamp(value, dt.timezone.utc).isoformat().replace('+00:00', 'Z')


@contextlib.contextmanager
def directory_fd(path):
    """No symlink component, including ancestors; no resolve/check/open race."""
    path = Path(path)
    if not path.is_absolute() or '..' in path.parts:
        raise OSError('Unsafe directory')
    fd = os.open('/', os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        for component in path.parts[1:]:
            child = os.open(component, os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=fd)
            os.close(fd)
            fd = child
        yield fd
    finally:
        os.close(fd)


def private_regular(info, maximum, source_digest=False):
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1
            or info.st_mode & (0o002 if source_digest else 0o022) or info.st_size > maximum):
        raise OSError('Unsafe file')


def bounded_file(path, maximum, *, source_digest=False):
    with directory_fd(Path(path).parent) as parent:
        fd = os.open(Path(path).name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=parent)
        with os.fdopen(fd, 'rb') as stream:
            before = os.fstat(stream.fileno())
            private_regular(before, maximum, source_digest=source_digest)
            data = stream.read(maximum + 1)
            after = os.fstat(stream.fileno())
            fields = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
            if len(data) > maximum or any(getattr(before, f) != getattr(after, f) for f in fields):
                raise OSError('Changed file')
            return data


class Audit:
    """Append-only bounded private JSONL; never retire or overwrite old records."""
    maximum = 16 * 1024**2

    def __init__(self, directory):
        self.directory = Path(directory)
        self.lock = threading.Lock()

    @contextlib.contextmanager
    def slot(self):
        if not self.lock.acquire(blocking=False):
            raise ReadError('AUDIT_UNAVAILABLE')
        try:
            with directory_fd(self.directory) as parent:
                try:
                    os.mkdir('mcp-read-audit', 0o700, dir_fd=parent)
                except FileExistsError:
                    pass
                fd = os.open('mcp-read-audit', os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent)
                try:
                    info = os.fstat(fd)
                    if info.st_uid != os.getuid() or info.st_mode & 0o077:
                        raise OSError('Unsafe audit directory')
                    log = os.open('reads.jsonl', os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, 0o600, dir_fd=fd)
                finally:
                    os.close(fd)
                with os.fdopen(log, 'ab', buffering=0) as stream:
                    info = os.fstat(stream.fileno())
                    private_regular(info, self.maximum)
                    if info.st_mode & 0o077:
                        raise OSError('Unsafe audit permissions')
                    fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    if info.st_size + 2048 > self.maximum:
                        raise OSError('Audit full')
                    yield stream
        except (OSError, ValueError):
            raise ReadError('AUDIT_UNAVAILABLE') from None
        finally:
            self.lock.release()

    @staticmethod
    def write(stream, record):
        data = (json.dumps(record, separators=(',', ':'), allow_nan=False) + '\n').encode()
        if len(data) > 2048 or stream.write(data) != len(data):
            raise ReadError('AUDIT_UNAVAILABLE')
        os.fsync(stream.fileno())


class Buckets:
    def __init__(self, clock=time.monotonic):
        self.clock, self.lock, self.state = clock, threading.Lock(), {}

    def take(self, name):
        with self.lock:
            now = self.clock()
            specs = [('global', 60, 10), (name, 12 if name in ('server_health', 'read_file', 'git_status', 'test_status', 'backup_status') else 30, 2 if name in ('server_health', 'read_file', 'git_status', 'test_status', 'backup_status') else 5)]
            if name == 'cancel_task':
                specs = [('global',60,10), (name,6,1)]
            denied = False
            for key, rate, burst in specs:
                tokens, previous = self.state.get(key, (burst, now))
                tokens = min(burst, tokens + max(0, now - previous) * rate / 60)
                denied |= tokens < 1
                self.state[key] = (max(0, tokens - 1), now)
            if denied:
                raise ReadError('RATE_LIMITED', 5 if name == 'server_health' else 2)


class Reads:
    inputs, outputs, descriptions = INPUTS, OUTPUTS, DESCRIPTIONS
    def __init__(self, directory, health_path=None, wall=time.time, monotonic=time.monotonic):
        self.directory = Path(directory)
        self.health_path = Path(health_path or Path.home() / '.local/state/server5-commandcenter/latest.json')
        self.wall, self.monotonic = wall, monotonic
        self.key = secrets.token_bytes(32)
        self.buckets = Buckets(monotonic)
        self.concurrent = threading.BoundedSemaphore(4)
        self.audit = Audit(directory)
        self.cache, self.cache_at = None, 0
        self.cache_lock = threading.Lock()

    def cursor(self, binding, position):
        value = [1, 'owner', binding, self.wall() + 900, position]
        body = json.dumps(value, separators=(',', ':'), allow_nan=False).encode()
        return base64.urlsafe_b64encode(body + hmac.digest(self.key, body, 'sha256')).rstrip(b'=').decode()

    def position(self, cursor, binding):
        if cursor is None:
            return None
        try:
            raw = base64.b64decode(cursor + '=' * (-len(cursor) % 4), altchars=b'-_', validate=True)
            body, signature = raw[:-32], raw[-32:]
            if not hmac.compare_digest(hmac.digest(self.key, body, 'sha256'), signature):
                raise ValueError()
            version, role, bound, expiry, position = json.loads(body)
            if version != 1 or role != 'owner' or bound != binding:
                raise ValueError()
            if expiry < self.wall():
                raise ReadError('CURSOR_EXPIRED')
            return position
        except ReadError:
            raise
        except Exception:
            raise ReadError('INVALID_ARGUMENT') from None

    @contextlib.contextmanager
    def db(self, deadline):
        remaining = deadline - self.monotonic()
        if remaining <= 0:
            raise ReadError('UNAVAILABLE')
        db = sqlite3.connect((self.directory / 'tasks.sqlite3').as_uri() + '?mode=ro', uri=True, timeout=min(3, remaining))
        db.row_factory = sqlite3.Row
        db.set_progress_handler(lambda: int(self.monotonic() >= deadline), 500)
        try:
            db.execute('PRAGMA query_only=ON')
            db.execute('BEGIN')
            yield db
        finally:
            db.close()

    def list_tasks(self, args, deadline):
        binding = ['list_tasks', args.limit, args.status]
        position = self.position(args.cursor, binding)
        with self.db(deadline) as db:
            if position is None:
                watermark = db.execute('SELECT coalesce(max(rowid),0) FROM tasks').fetchone()[0]
                snapshot = utc(self.wall())
                last = None
            else:
                watermark, snapshot, last = position
            where, params = ['rowid<=?'], [watermark]
            if args.status is not None:
                where.append('status=?'); params.append(args.status)
            if last is not None:
                where.append('(created,id)<(?,?)'); params.extend(last)
            params.append(args.limit + 1)
            rows = db.execute('SELECT id,status,created,started,finished,exit_code,cancel FROM tasks WHERE '
                              + ' AND '.join(where) + ' ORDER BY created DESC,id DESC LIMIT ?', params).fetchall()
        items = []
        for row in rows[:args.limit]:
            item = dict(row)
            for key in ('created', 'started', 'finished'):
                item[key] = utc(item[key]) if item[key] is not None else None
            if item['cancel'] not in (0, 1):
                raise ReadError('UNAVAILABLE')
            item['cancel'] = bool(item['cancel'])
            items.append(item)
        next_cursor = None
        if len(rows) > args.limit:
            last_row = rows[args.limit - 1]
            next_cursor = self.cursor(binding, [watermark, snapshot, [last_row['created'], last_row['id']]])
        return dict(schema_version=1, items=items, next_cursor=next_cursor, snapshot_at=snapshot)

    @staticmethod
    def label(text):
        # Positive selection only. Payload is NEVER copied to output, even when
        # recognized. ANSI/control bytes, oversized and legacy text fail closed.
        if len(text) > 16000 or any(ord(c) < 32 and c not in '\n\r\t' for c in text):
            return 'details_withheld'
        if text == 'Codex gestart; één actieve taak. Zonder Bubblewrap volgens experimentele afspraak.':
            return 'worker_started'
        try:
            value = json.loads(text)
            if type(value) is not dict or type(value.get('type')) is not str:
                return 'details_withheld'
            return {'thread.started': 'execution_event', 'turn.started': 'execution_event',
                    'turn.completed': 'turn_completed', 'turn.failed': 'turn_failed',
                    'error': 'turn_failed', 'item.started': 'execution_event',
                    'item.updated': 'execution_event', 'item.completed': 'execution_event'}.get(value['type'], 'details_withheld')
        except (ValueError, RecursionError):
            return 'details_withheld'

    def task_logs(self, args, deadline):
        binding = ['task_logs', args.limit, args.task_id]
        position = self.position(args.cursor, binding)
        with self.db(deadline) as db:
            if not db.execute('SELECT 1 FROM tasks WHERE id=?', (args.task_id,)).fetchone():
                raise ReadError('NOT_FOUND')
            watermark, last = position if position else (db.execute('SELECT coalesce(max(seq),0) FROM events WHERE task=?', (args.task_id,)).fetchone()[0], 0)
            rows = db.execute('SELECT seq,at,substr(text,1,16001) AS text FROM events WHERE task=? AND seq>? AND seq<=? ORDER BY seq LIMIT ?',
                              (args.task_id, last, watermark, args.limit + 1)).fetchall()
        entries = []
        for row in rows[:args.limit]:
            kind = self.label(row['text'])
            entries.append(dict(seq=row['seq'], at=utc(row['at']), kind=kind, message=LABELS[kind]))
        more = len(rows) > args.limit
        # Include the cursor and both SDK representations in the byte budget.
        # Stop at the last actually published seq; never skip withheld entries.
        while True:
            result = dict(schema_version=1, task_id=args.task_id, entries=entries,
                          next_cursor=self.cursor(binding, [watermark, entries[-1]['seq']]) if more else None,
                          snapshot_complete=not more, details_withheld=any(e['kind'] == 'details_withheld' for e in entries))
            if len(json.dumps(result, ensure_ascii=True).encode()) * 2 + 1024 <= 16384:
                return result
            entries.pop()
            more = True
            if not entries:
                raise ReadError('UNAVAILABLE')

    def server_health(self, args, deadline):
        with self.cache_lock:
            now = self.monotonic()
            if self.cache is None or now - self.cache_at >= 5:
                self.cache = self.read_health()
                self.cache_at = now
            result = dict(self.cache)
        result['issues'] = list(result['issues'])
        observed = result['observed_at']
        if observed is not None:
            age = self.wall() - dt.datetime.fromisoformat(observed.replace('Z', '+00:00')).timestamp()
            if age > HEALTH_MAX_AGE_SECONDS or age < -30:
                result.update(stale=True, status='unknown')
                if 'snapshot_stale' not in result['issues']:
                    result['issues'].append('snapshot_stale')
        return result

    def read_health(self):
        unknown = dict(schema_version=1, host='server5', observed_at=None, stale=True, status='unknown',
                       memory_available_bytes=None, root_free_bytes=None, load=None, reboot_required=None,
                       ssh_available=None, ntp_synchronized='unknown', issues=['collector_unavailable'])
        try:
            value = json.loads(bounded_file(self.health_path, 65536).decode('utf-8'))
            if type(value) is not dict or type(value.get('schema_version')) is not int or value['schema_version'] != 2 or value['hostname'] != 'server5':
                return unknown
            if value['status'] not in ('ok', 'warning', 'error', 'unknown'):
                return unknown
            observed = dt.datetime.fromisoformat(value['utc'].replace('Z', '+00:00'))
            if observed.utcoffset() != dt.timedelta(0):
                return unknown
            result = dict(schema_version=1, host='server5', observed_at=utc(observed.timestamp()), stale=False,
                          **{key: value[key] for key in ('status', 'memory_available_bytes', 'root_free_bytes', 'load',
                                                       'reboot_required', 'ssh_available', 'ntp_synchronized')})
            issues = []
            mapping = {'available_memory_below_2GiB': 'low_memory', 'root_free_below_15GiB': 'low_disk',
                       'firmware_metadata_refresh_failed': 'firmware_metadata_refresh_failed',
                       'reboot_required': 'reboot_required', 'ssh_unit_failed': 'ssh_unavailable',
                       'ssh_not_active': 'ssh_unavailable', 'ntp_not_synchronized': 'ntp_unsynchronized'}
            for category in ('errors', 'warnings', 'collector_errors'):
                codes = value[category]
                if type(codes) is not list or len(codes) > 256 or any(type(x) is not str for x in codes):
                    return unknown
                for code in codes:
                    issue = mapping.get(code, 'collector_unavailable' if category == 'collector_errors' else 'other_system_failure')
                    if issue not in issues:
                        issues.append(issue)
            # Classification is recomputed; a malformed "ok" must not hide errors.
            result['status'] = ('unknown' if value['collector_errors'] else 'error' if value['errors'] else 'warning' if value['warnings'] else 'ok')
            result['issues'] = issues
            return HealthOutput.model_validate(result).model_dump()
        except Exception:
            return unknown

    def dispatch(self, name, arguments):
        start = self.monotonic()
        acquired = False
        code, retry, result = 'OK', None, None
        target, args = None, None
        try:
            try:
                self.buckets.take(name)
                acquired = self.concurrent.acquire(blocking=False)
                if not acquired:
                    raise ReadError('RATE_LIMITED', 1)
                if os.path.lexists(self.directory / 'mcp-reads.disabled') or (name not in INPUTS and os.path.lexists(self.directory / 'mcp-extended.disabled')):
                    raise ReadError('DISABLED')
                try:
                    args = self.inputs[name].model_validate(arguments)
                except Exception:
                    raise ReadError('INVALID_ARGUMENT') from None
                target = args.task_id if name == 'task_logs' else args.file_id if name == 'read_file' else None
                result = getattr(self, name)(args, start + 4)
                result = self.outputs[name].model_validate(result).model_dump()
                if self.monotonic() - start >= 4:
                    raise ReadError('UNAVAILABLE')
                # Count BOTH MCP representations, not just structuredContent.
                if len(json.dumps(result, ensure_ascii=True).encode()) * 2 + 1024 > (16384 if name == 'task_logs' else 65536):
                    raise ReadError('UNAVAILABLE')
            except ReadError as exc:
                code, retry = exc.code, exc.retry
            except Exception:
                code = 'UNAVAILABLE'
            # Even invalid calls consume budgets and audit space. No content is
            # released until the audit record is durably appended.
            with self.audit.slot() as stream:
                self.audit.write(stream, dict(utc=utc(self.wall()), call_id=secrets.token_hex(16), principal='owner',
                    tool=name, target=target, outcome=code,
                    stale=result['stale'] if code == 'OK' and name == 'server_health' else None,
                    status_filter=args.status if name == 'list_tasks' and args is not None else None,
                    items=len(result.get('items', result.get('entries', []))) if code == 'OK' else 0,
                    bytes=len(json.dumps(result).encode()) if code == 'OK' else 0,
                    duration_ms=max(0, int((self.monotonic() - start) * 1000))))
            if self.monotonic() - start >= 5:
                raise ReadError('UNAVAILABLE')
        except ReadError as exc:
            code, retry = exc.code, exc.retry
        except Exception:
            code, retry = 'AUDIT_UNAVAILABLE', None
        finally:
            if acquired:
                self.concurrent.release()
        if code != 'OK':
            payload = {'code': code, 'retry_after_seconds': retry}
            return CallToolResult(isError=True, content=[TextContent(type='text', text=json.dumps(payload))])
        return CallToolResult(isError=False, structuredContent=result,
                              content=[TextContent(type='text', text=json.dumps(result))])


class ReadsMCP(FastMCP):
    """Keep the SDK transport/auth; intercept new reads before SDK coercion/errors."""
    def __init__(self, *args, reads=None, **kwargs):
        self.reads = reads
        super().__init__(*args, **kwargs)

    async def list_tools(self):
        tools = await super().list_tools()
        if self.reads is not None:
            annotations = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)
            tools += [Tool(name=name, description=self.reads.descriptions[name], inputSchema=schema(self.reads.inputs[name]),
                           outputSchema=schema(self.reads.outputs[name]), annotations=annotations) for name in self.reads.inputs]
        return tools

    async def call_tool(self, name, arguments):
        if self.reads is not None and name in self.reads.inputs:
            return await anyio.to_thread.run_sync(self.reads.dispatch, name, arguments)
        return await super().call_tool(name, arguments)
