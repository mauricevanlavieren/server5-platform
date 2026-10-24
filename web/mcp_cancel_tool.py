"""Strict MCP dispatch for optional cancellation, separate from broker dependencies."""
import json
import threading
from typing import Annotated, Literal
import anyio
from pydantic import Field
from mcp.types import CallToolResult, TextContent, Tool, ToolAnnotations
from mcp_reads import Model, ID, Status, ReadsMCP, Buckets, ReadError, schema
from mcp_cancel import Cancellation, CancelError

class CancelInput(Model):
    task_id: ID
    confirmed: bool = Field(json_schema_extra={"const":True})
    request_id: ID
    confirmation_id: Annotated[str,Field(min_length=43,max_length=128,pattern=r'^[A-Za-z0-9_-]+$')]

class CancelOutput(Model):
    schema_version: Literal[1]
    task_id: ID
    request_id: ID
    outcome: Literal['queued_cancelled','cancellation_requested','already_terminal']
    status: Status
    cancel_requested: bool
    stopped: bool
    effects_reverted: Literal[False]

class CancelTools:
    def __init__(self,directory):
        self.service=Cancellation(directory)
        self.buckets=Buckets()
        self.lock=threading.Lock()
    def dispatch(self,arguments):
        acquired=False
        try:
            self.buckets.take('cancel_task')
            acquired=self.lock.acquire(blocking=False)
            if not acquired:raise CancelError('RATE_LIMITED')
            try:args=CancelInput.model_validate(arguments)
            except Exception:raise CancelError('INVALID_ARGUMENT') from None
            result=self.service.cancel(**args.model_dump())
            result=CancelOutput.model_validate(result).model_dump()
            return CallToolResult(isError=False,structuredContent=result,content=[TextContent(type='text',text=json.dumps(result))])
        except Exception as exc:
            code=exc.code if isinstance(exc,ReadError) else str(exc) if isinstance(exc,CancelError) else 'UNAVAILABLE'
            return CallToolResult(isError=True,content=[TextContent(type='text',text=json.dumps({'code':code,'retry_after_seconds':None}))])
        finally:
            if acquired:self.lock.release()

class CommandMCP(ReadsMCP):
    def __init__(self,*args,cancellation=None,**kwargs):
        self.cancellation=cancellation
        super().__init__(*args,**kwargs)
    async def list_tools(self):
        result=await super().list_tools()
        if self.cancellation is not None:
            result.append(Tool(name='cancel_task',description='Stop alleen na expliciete onafhankelijke eigenaar-webbevestiging (60s), gebonden aan taak-ID en request_id. Geen terugdraaiing van effecten. Running betekent alleen stop aangevraagd; lees task_status voor actuele toestand.',
                inputSchema=schema(CancelInput),outputSchema=schema(CancelOutput),
                annotations=ToolAnnotations(readOnlyHint=False,destructiveHint=True,idempotentHint=True,openWorldHint=False)))
        return result
    async def call_tool(self,name,arguments):
        if name=='cancel_task' and self.cancellation is not None:
            return await anyio.to_thread.run_sync(self.cancellation.dispatch,arguments)
        return await super().call_tool(name,arguments)
