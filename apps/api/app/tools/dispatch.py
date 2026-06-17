"""Tool dispatch (ticket 4.07).

Validates raw LLM-supplied arguments against the tool's Pydantic schema, runs
``execute``, and converts any failure into ``{"error": "<message>"}`` so the LLM
can apologise and recover rather than the call breaking.
"""

from __future__ import annotations

from typing import Any

import structlog
from pydantic import ValidationError

from app.tools.base import Tool, ToolContext

logger = structlog.get_logger(__name__)


def _format_validation_error(exc: ValidationError) -> str:
    parts = [
        f"{'.'.join(str(p) for p in err['loc']) or 'args'}: {err['msg']}"
        for err in exc.errors()
    ]
    return "invalid arguments: " + "; ".join(parts)


async def run_tool(
    tool: Tool, ctx: ToolContext, raw_args: dict[str, Any] | None
) -> dict[str, Any]:
    """Validate args, execute the tool, and always return a JSON-able dict."""

    try:
        args = tool.parameters_schema.model_validate(raw_args or {})
    except ValidationError as exc:
        logger.info("tool_args_invalid", tool=tool.name)
        return {"error": _format_validation_error(exc)}

    try:
        result = await tool.execute(ctx, args)
    except Exception as exc:
        logger.warning("tool_execution_failed", tool=tool.name, error=str(exc))
        return {"error": str(exc)}

    return result if isinstance(result, dict) else {"result": result}
