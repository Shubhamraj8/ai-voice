"""Tests for tenant access-window expiry (ticket 5.03). DB + audit mocked."""

import uuid
from unittest.mock import AsyncMock

from app.services import subscription_expiry as se


async def test_expire_pauses_lapsed_tenants(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(se, "get_pool", lambda: pool)
    audit = AsyncMock()
    monkeypatch.setattr(se, "log_system_action", audit)
    conn.fetch.return_value = [{"id": uuid.uuid4()}, {"id": uuid.uuid4()}]

    count = await se.expire_lapsed_tenants()

    assert count == 2
    assert audit.await_count == 2
    # the UPDATE only targets active, lapsed tenants
    sql = conn.fetch.await_args.args[0]
    assert "status = 'active'" in sql and "paid_until < now()" in sql


async def test_expire_noop_when_none_lapsed(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(se, "get_pool", lambda: pool)
    audit = AsyncMock()
    monkeypatch.setattr(se, "log_system_action", audit)
    conn.fetch.return_value = []

    count = await se.expire_lapsed_tenants()

    assert count == 0
    audit.assert_not_awaited()


async def test_expire_swallows_errors(monkeypatch):
    def _boom():
        raise RuntimeError("no pool")

    monkeypatch.setattr(se, "get_pool", _boom)

    assert await se.expire_lapsed_tenants() == 0
