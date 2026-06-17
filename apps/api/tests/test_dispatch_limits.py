"""Tests for per-call rate limits + idempotency (ticket 4.12). Redis mocked."""

import uuid
from unittest.mock import AsyncMock

from app.tools import dispatch
from app.tools.base import Tool, ToolContext
from pydantic import BaseModel


class _Args(BaseModel):
    x: int = 0


class RateTool(Tool):
    name = "rateTool"
    description = "test tool"
    parameters_schema = _Args
    max_per_call = 2

    async def execute(self, ctx, args):
        return {"ok": True}


def _ctx():
    return ToolContext(call_id=uuid.uuid4())


def _patch_cache(monkeypatch, *, cached=None, counts=None, incr_value=None):
    monkeypatch.setattr(dispatch.cache, "get_json", AsyncMock(return_value=cached))
    monkeypatch.setattr(dispatch.cache, "set_json", AsyncMock())
    if counts is not None:
        monkeypatch.setattr(
            dispatch.cache, "incr_with_ttl", AsyncMock(side_effect=counts)
        )
    else:
        monkeypatch.setattr(
            dispatch.cache, "incr_with_ttl", AsyncMock(return_value=incr_value)
        )


async def test_rate_limit_blocks_after_max(monkeypatch):
    _patch_cache(monkeypatch, counts=[1, 2, 3])
    tool = RateTool()
    execute = AsyncMock(return_value={"ok": True})
    tool.execute = execute
    ctx = _ctx()

    r1 = await dispatch.run_tool(tool, ctx, {})
    r2 = await dispatch.run_tool(tool, ctx, {})
    r3 = await dispatch.run_tool(tool, ctx, {})

    assert r1 == {"ok": True}
    assert r2 == {"ok": True}
    assert "error" in r3 and "maximum" in r3["error"]
    assert execute.await_count == 2  # 3rd never executed


async def test_idempotency_hit_returns_cached_without_executing(monkeypatch):
    _patch_cache(monkeypatch, cached={"cached": True}, incr_value=1)
    tool = RateTool()
    execute = AsyncMock()
    tool.execute = execute

    result = await dispatch.run_tool(tool, _ctx(), {}, idempotency_key="k1")

    assert result == {"cached": True}
    execute.assert_not_awaited()


async def test_idempotency_caches_result(monkeypatch):
    _patch_cache(monkeypatch, cached=None, incr_value=1)
    set_json = dispatch.cache.set_json

    result = await dispatch.run_tool(RateTool(), _ctx(), {}, idempotency_key="k2")

    assert result == {"ok": True}
    set_json.assert_awaited_once()
    assert set_json.await_args.args[0] == "idem:k2"


async def test_rate_limit_skipped_when_redis_unavailable(monkeypatch):
    _patch_cache(monkeypatch, incr_value=None)  # INCR returns None → disabled
    tool = RateTool()
    execute = AsyncMock(return_value={"ok": True})
    tool.execute = execute
    ctx = _ctx()

    for _ in range(5):
        await dispatch.run_tool(tool, ctx, {})

    assert execute.await_count == 5  # no enforcement when Redis is off


async def test_no_call_id_skips_rate_limit(monkeypatch):
    _patch_cache(monkeypatch, incr_value=1)
    incr = dispatch.cache.incr_with_ttl

    await dispatch.run_tool(RateTool(), ToolContext(), {})  # call_id is None

    incr.assert_not_awaited()
