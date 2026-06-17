"""Tool dispatch (tickets 4.07, 4.12).

Validates raw LLM-supplied arguments against the tool's Pydantic schema, enforces
per-call rate limits and idempotency via Redis, runs ``execute``, and converts
any failure into ``{"error": "<message>"}`` so the LLM can apologise and recover
rather than the call breaking.

Order: idempotency cache hit → validate args → rate-limit (INCR) → execute →
cache the result for idempotency → log. Redis is best-effort: when it is
unavailable, rate limiting and idempotency simply don't apply.
"""

from __future__ import annotations

import json
from typing import Any

import structlog
from pydantic import ValidationError

from app.services import cache
from app.tools.base import Tool, ToolContext

logger = structlog.get_logger(__name__)

RATE_LIMIT_TTL_S = 3600  # per-call counters; calls are far shorter than this
IDEMPOTENCY_TTL_S = 600  # 10 minutes


def _format_validation_error(exc: ValidationError) -> str:
    parts = [
        f"{'.'.join(str(p) for p in err['loc']) or 'args'}: {err['msg']}"
        for err in exc.errors()
    ]
    return "invalid arguments: " + "; ".join(parts)


async def run_tool(
    tool: Tool,
    ctx: ToolContext,
    raw_args: dict[str, Any] | None,
    *,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """Validate args, enforce limits, execute, and always return a JSON-able dict."""

    # 1. Idempotency: a repeated attempt (same tool-call id) returns its result
    #    without re-executing the side effect.
    idem_cache_key = f"idem:{idempotency_key}" if idempotency_key else None
    if idem_cache_key:
        cached = await cache.get_json(idem_cache_key)
        if isinstance(cached, dict):
            logger.info("tool_idempotent_hit", tool=tool.name)
            return cached

    # 2. Validate arguments (don't consume the rate-limit quota on bad args).
    try:
        args = tool.parameters_schema.model_validate(raw_args or {})
    except ValidationError as exc:
        logger.info("tool_args_invalid", tool=tool.name)
        return {"error": _format_validation_error(exc)}

    # 3. Per-call rate limit.
    if ctx.call_id is not None and tool.max_per_call is not None:
        count = await cache.incr_with_ttl(
            f"rl:{ctx.call_id}:{tool.name}", ttl_s=RATE_LIMIT_TTL_S
        )
        if count is not None and count > tool.max_per_call:
            logger.info("tool_rate_limited", tool=tool.name, count=count)
            return {
                "error": (
                    f"The {tool.name} tool has been used the maximum number of "
                    "times this call."
                )
            }

    # 4. Execute.
    try:
        result = await tool.execute(ctx, args)
        final = result if isinstance(result, dict) else {"result": result}
    except Exception as exc:
        logger.warning("tool_execution_failed", tool=tool.name, error=str(exc))
        final = {"error": str(exc)}

    # 5. Cache the result so retries of this attempt don't re-execute.
    if idem_cache_key:
        await cache.set_json(idem_cache_key, final, ttl_s=IDEMPOTENCY_TTL_S)

    # 6. Log dispatch (arg keys only — values may be sensitive — + result size).
    logger.info(
        "tool_dispatched",
        tool=tool.name,
        arg_keys=sorted(args.model_dump().keys()),
        result_bytes=len(json.dumps(final, default=str)),
    )
    return final
