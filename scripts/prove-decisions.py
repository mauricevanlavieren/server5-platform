#!/usr/bin/env python3
"""Local simulated task + actual CLI waiter + actual MCP dispatch. No service restart."""
import asyncio
import json
from pathlib import Path
import subprocess
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'web'))
from commandcenter import Store
from decisions import Decisions
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
ROOT=Path(__file__).resolve().parents[1]
async def main():
    with tempfile.TemporaryDirectory(prefix='s5-decision-proof-') as td:
        state=Path(td);store=Store(state);task=store.submit('Simulated local decision and resume','decision_simulation_0001');store.claim()
        d=Decisions(state)
        subprocess.run([sys.executable,str(ROOT/'web/decisions.py'),'--state',td,'ask','decision_simulation_0001','Welke testkleur?','--task-id',task['id'],'--options','["groen","blauw"]'],check=True,capture_output=True)
        waiter=subprocess.Popen([sys.executable,str(ROOT/'web/decisions.py'),'--state',td,'wait','decision_simulation_0001','--timeout','5'],stdout=subprocess.PIPE,text=True)
        # Real adapter registration, intercept only ASGI construction to retain the instance.
        import mcp_adapter
        original=FastMCP.streamable_http_app;instances=[]
        def retain(instance):instances.append(instance);return original(instance)
        FastMCP.streamable_http_app=retain
        try:mcp_adapter.create_app(state,token='simulation-only-not-a-credential',enable_decisions=True)
        finally:FastMCP.streamable_http_app=original
        await instances[0].call_tool('answer_decision',{'request_id':'decision_simulation_0001','answer_id':'answer_simulation_00001','answer':'groen'})
        out,_=waiter.communicate(timeout=8);assert waiter.returncode==0
        response=json.loads(out);assert response['answer']=='groen'
        store.finish(task['id'],'succeeded','Hervat met testkleur groen',0)
        evidence={'scope':'isolated simulation on server5; real SQLite/CLI process/MCP tool dispatch, no actual ChatGPT activation or Codex execution','request':response,'resumed':store.get(task['id'])['status'],'tools':[t.name for t in await instances[0].list_tools()]}
        (ROOT/'docs/decision-mvp/simulation.json').write_text(json.dumps(evidence,indent=2))
asyncio.run(main())
