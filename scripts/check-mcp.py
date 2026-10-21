#!/usr/bin/env python3
"""Authenticated read-only smoke test; never prints credentials or task content."""
import asyncio
import logging
from pathlib import Path
import sqlite3

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def check():
    token = (Path.home() / '.config/server5-commandcenter/mcp-token').read_text().strip()
    path = Path.home() / '.local/state/server5-commandcenter/mvp/tasks.sqlite3'
    with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) as db:
        row = db.execute('SELECT id FROM tasks ORDER BY created DESC LIMIT 1').fetchone()
    async with streamablehttp_client('http://127.0.0.1:8796/mcp',
            headers={'Authorization': 'Bearer ' + token}) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            assert {tool.name for tool in tools.tools} == {'task_status', 'task_result'}
            if row:
                for tool in ('task_status', 'task_result'):
                    result = await session.call_tool(tool, {'task_id': row[0]})
                    assert not result.isError
            rejected = await session.call_tool('start_task', {})
            assert rejected.isError
    print('MCP smoke PASS: initialisatie, discovery, leestoegang en schrijfweigering; geen taak ingediend.')


if __name__ == '__main__':
    logging.disable(logging.CRITICAL)
    asyncio.run(check())
