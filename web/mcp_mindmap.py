"""Fixed-path current published map snapshot; no network or caller paths."""
import hashlib
import json
import re
from typing import Literal
from pydantic import Field
from mcp_reads import Model, Date, ReadError, bounded_file, utc
from commandcenter import redact

class SnapshotInput(Model):
    pass

class MapNode(Model):
    path: str = Field(max_length=80)
    ids: list[str] = Field(max_length=16)
    text: str = Field(max_length=2000)
    status: Literal['pending', 'active', 'blocked', 'done']
    block: dict[str, str] | None = None

class Project(Model):
    id: str
    status: Literal['ACTIEF', 'WACHTEND', 'GEBLOKKEERD', 'VOLTOOID']
    current_steps: list[str]
    node_status: Literal['pending', 'active', 'blocked', 'done']
    valid: bool

class SnapshotOutput(Model):
    schema_version: Literal[1]
    snapshot_at: Date
    source_sha256: str
    publication_sha256: str
    consistent: bool
    project_invariants_valid: bool
    node_count: int
    nodes: list[MapNode] = Field(max_length=300)
    projects: list[Project] = Field(max_length=50)
    content_is_untrusted: Literal[True]


def snapshot(root, forbidden='', wall=None):
    # The organic browser fetches this exact publication; no legacy Markdown/map.json.
    map_path = root / 'mindmap/public/current-projects.json'
    try:
        raw = bounded_file(map_path, 524288)
        tree = json.loads(raw)['root']
        nodes, projects, seen = [], [], set()
        statuses = {'pending': 'WACHTEND', 'active': 'ACTIEF',
                    'blocked': 'GEBLOKKEERD', 'done': 'VOLTOOID'}

        def safe_text(text):
            if not isinstance(text, str) or len(text) > 2000 or any(ord(c) < 32 for c in text):
                raise ValueError()
            if redact(text) != text or (forbidden and forbidden in text) or re.search(r'sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|tskey-|-----BEGIN .*PRIVATE KEY', text):
                raise ValueError()
            return text

        def walk(node, path, level):
            if len(nodes) >= 300 or level > 30:
                raise ValueError()
            ident = safe_text(node['id'])
            if not ident or ident in seen or node['status'] not in statuses:
                raise ValueError()
            seen.add(ident)
            block = node.get('block')
            if block is not None:
                if set(block) != {'cause', 'solution', 'next_action'}:
                    raise ValueError()
                block = {k: safe_text(v) for k, v in block.items()}
            nodes.append(dict(path=path, ids=[ident], text=safe_text(node['title']),
                              status=node['status'], block=block))
            for i, child in enumerate(node['children'], 1):
                walk(child, path + '.' + str(i), level + 1)

        walk(tree, '1', 1)
        # A collection root groups independent projects; the older organic format
        # has a single project as its root. Pending ancestors are neutral in the UI.
        roots = tree['children'] if tree['id'] == 'CURRENT-PROJECTS' else [tree]
        def descendants(node):
            yield node
            for child in node['children']:
                yield from descendants(child)
        for project in roots:
            branch = list(descendants(project))
            active = [n for n in branch if n['status'] == 'active']
            blocked = [n for n in branch if n['status'] == 'blocked']
            state = project['status']
            if state == 'pending':
                state = 'active' if active else 'blocked' if blocked else 'pending'
            def depth(n, level=0):
                yield n, level
                for c in n['children']:
                    yield from depth(c, level + 1)
            levels = list(depth(project))
            valid = (len(active) <= 1
                     and (not active or next(d for n, d in levels if n is active[0]) == max(d for n, d in levels))
                     and (project['status'] != 'active' or len(active) == 1) and all(not n['children'] for n in active)
                     and all(n.get('block') and all(n['block'].values()) for n in blocked)
                     and all(not n['children'] for n in branch if n['status'] == 'done')
                     and (project['status'] != 'done' or len(branch) == 1))
            projects.append(dict(id=project['id'], status=statuses[state],
                                 node_status=project['status'],
                                 current_steps=[n['id'] for n in active], valid=valid))
        # Re-read the same browser publication to detect concurrent writes.
        publication = bounded_file(map_path, 524288)
        result = dict(schema_version=1, snapshot_at=utc(wall()),
            source_sha256=hashlib.sha256(raw).hexdigest(),
            publication_sha256=hashlib.sha256(publication).hexdigest(),
            consistent=raw == publication,
            project_invariants_valid=all(p['valid'] for p in projects), node_count=len(nodes),
            nodes=nodes, projects=projects, content_is_untrusted=True)
        if len(json.dumps(result, ensure_ascii=True).encode()) * 2 + 1024 > 65536:
            raise ReadError('OUTPUT_LIMIT')
        return result
    except ReadError:
        raise
    except Exception:
        raise ReadError('CONTENT_WITHHELD') from None
