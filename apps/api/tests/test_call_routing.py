"""Unit tests for per-tenant call routing (ticket 3.09). DB mocked."""

import uuid

from app.services import call_routing


async def test_resolve_returns_route(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    tenant_id = uuid.uuid4()
    agent_id = uuid.uuid4()
    conn.fetchrow.return_value = {
        "agent_id": agent_id,
        "tenant_id": tenant_id,
        "stt": "deepgram",
        "tts": "deepgram",
        "llm": "deepseek_native",
    }
    monkeypatch.setattr(call_routing, "get_pool", lambda: pool)

    route = await call_routing.resolve_agent_by_number("+911234567890")

    assert route is not None
    assert route.tenant_id == tenant_id
    assert route.agent_id == agent_id
    assert route.stt == "deepgram"
    assert route.llm == "deepseek_native"
    assert conn.fetchrow.await_args.args[1] == "+911234567890"


async def test_resolve_returns_none_when_no_match(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    conn.fetchrow.return_value = None
    monkeypatch.setattr(call_routing, "get_pool", lambda: pool)

    assert await call_routing.resolve_agent_by_number("+910000000000") is None


async def test_resolve_returns_none_for_empty_number():
    assert await call_routing.resolve_agent_by_number("") is None


async def test_resolve_swallows_db_error(monkeypatch):
    def _boom():
        raise RuntimeError("no pool")

    monkeypatch.setattr(call_routing, "get_pool", _boom)
    assert await call_routing.resolve_agent_by_number("+911234567890") is None
