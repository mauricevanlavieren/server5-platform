#!/usr/bin/env python3
"""Authenticated read-only smoke test; never prints credentials or task content."""
import asyncio
import argparse
import logging
import json
from pathlib import Path
import sqlite3

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def check(expect_start_task=False, expect_read_tools=False, expect_extended_tools=False):
    token = (Path.home() / '.config/server5-commandcenter/mcp-token').read_text().strip()
    path = Path.home() / '.local/state/server5-commandcenter/mvp/tasks.sqlite3'
    with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) as db:
        row = db.execute('SELECT id FROM tasks ORDER BY created DESC LIMIT 1').fetchone()
    async with streamablehttp_client('http://127.0.0.1:8796/mcp',
            headers={'Authorization': 'Bearer ' + token}) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            expected = {'task_status', 'task_result'} | ({'start_task'} if expect_start_task else set())
            expected |= {'list_tasks', 'task_logs', 'server_health'} if expect_read_tools or expect_extended_tools else set()
            expected |= {'read_file','task_progress','git_status','test_status','backup_status','mindmap_snapshot'} if expect_extended_tools else set()
            assert {tool.name for tool in tools.tools} == expected
            if expect_start_task:
                start = next(tool for tool in tools.tools if tool.name == 'start_task')
                assert not start.annotations.readOnlyHint and start.annotations.destructiveHint
            if expect_read_tools:
                for name, args in [('list_tasks', {'limit': 2}), ('server_health', {})] + ([('task_logs', {'task_id': row[0], 'limit': 2})] if row else []):
                    result = await session.call_tool(name, args)
                    if result.isError:
                        error = json.loads(result.content[0].text)
                        code = error.get('code')
                        assert code in {'INVALID_ARGUMENT','UNAVAILABLE','AUDIT_UNAVAILABLE','RATE_LIMITED','DISABLED','NOT_FOUND','CURSOR_EXPIRED'}
                        raise AssertionError(name + ': ' + code)
                    assert result.structuredContent['schema_version'] == 1
            if expect_extended_tools:
                for name, args in [('read_file',{'file_id':'mcp_phase3'}),('task_progress',{}),('git_status',{}),('test_status',{}),('backup_status',{})]:
                    await asyncio.sleep(1.1)
                    result = await session.call_tool(name,args)
                    assert not result.isError, name + ': read failed'
                    assert result.structuredContent['schema_version'] == 1
            if row:
                for tool in ('task_status', 'task_result'):
                    result = await session.call_tool(tool, {'task_id': row[0]})
                    assert not result.isError
    print('MCP smoke PASS: initialisatie, verwachte discovery en leestoegang; start_task NIET aangeroepen, geen taak ingediend.')


if __name__ == '__main__':
    logging.disable(logging.CRITICAL)
    parser = argparse.ArgumentParser()
    parser.add_argument('--expect-start-task', action='store_true')
    parser.add_argument('--expect-read-tools', action='store_true')
    parser.add_argument('--expect-extended-tools', action='store_true')
    args = parser.parse_args()
    asyncio.run(check(args.expect_start_task, args.expect_read_tools, args.expect_extended_tools))
