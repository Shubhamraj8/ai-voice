"""Pipecat wiring for the tool framework (ticket 4.07).

Turns registered ``Tool`` instances into a pipecat ``ToolsSchema`` for the LLM
context and registers handlers on the LLM service. Each handler dispatches via
``run_tool``, logs the call to ``call_messages`` (role ``tool``), and returns the
result to pipecat's tool-call loop.
"""

from __future__ import annotations

import json

import structlog
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema

from app.services.calls import record_turn
from app.tools.base import Tool, ToolContext
from app.tools.dispatch import run_tool
from app.tools.schema import function_schema_dict

logger = structlog.get_logger(__name__)


def build_tools_schema(tools: list[Tool]) -> ToolsSchema | None:
    """Build a pipecat ToolsSchema from tools, or None when there are none."""

    if not tools:
        return None

    schemas = []
    for tool in tools:
        spec = function_schema_dict(tool)
        schemas.append(
            FunctionSchema(
                name=spec["name"],
                description=spec["description"],
                properties=spec["parameters"]["properties"],
                required=spec["parameters"]["required"],
            )
        )
    return ToolsSchema(standard_tools=schemas)


def _make_handler(tool: Tool, ctx: ToolContext):
    async def handler(params) -> None:
        raw_args = dict(params.arguments or {})
        result = await run_tool(tool, ctx, raw_args)

        if ctx.call_id is not None:
            await record_turn(
                call_id=ctx.call_id,
                tenant_id=ctx.tenant_id,
                role="tool",
                content=json.dumps(
                    {"tool": tool.name, "args": raw_args, "result": result}
                ),
            )

        await params.result_callback(result)

    return handler


def register_tools(llm, tools: list[Tool], ctx: ToolContext) -> None:
    """Register a dispatching handler on ``llm`` for each tool."""

    for tool in tools:
        llm.register_function(tool.name, _make_handler(tool, ctx))
        logger.info("tool_registered", tool=tool.name)
