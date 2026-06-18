"""Tests for daily usage rollup (ticket 5.06). DB + ledger mocked."""

import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock

from app.services import usage_aggregation as ua


class _FakeTxn:
    async def __aenter__(self):
        return None

    async def __aexit__(self, *args):
        return False


async def test_aggregates_overage(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(ua, "get_pool", lambda: pool)
    conn.transaction = MagicMock(return_value=_FakeTxn())
    conn.fetch.return_value = [
        {
            "tenant_id": uuid.uuid4(),
            "day_minutes": 120.0,
            "day_cost": 0.5,
            "month_minutes": 350.0,
            "included_minutes": 300,
        }
    ]
    log = AsyncMock()
    monkeypatch.setattr(ua, "log_billing_event", log)

    count = await ua.aggregate_daily_usage(date(2026, 7, 18))

    assert count == 1
    conn.execute.assert_awaited_once()  # idempotent delete-before-insert
    meta = log.await_args.kwargs["metadata"]
    assert meta["date"] == "2026-07-18"
    assert meta["overage_minutes"] == 50.0  # 350 month-to-date − 300 included
    assert meta["day_minutes"] == 120.0


async def test_no_overage_when_within_plan(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(ua, "get_pool", lambda: pool)
    conn.transaction = MagicMock(return_value=_FakeTxn())
    conn.fetch.return_value = [
        {
            "tenant_id": uuid.uuid4(),
            "day_minutes": 40.0,
            "day_cost": 0.2,
            "month_minutes": 200.0,
            "included_minutes": 300,
        }
    ]
    log = AsyncMock()
    monkeypatch.setattr(ua, "log_billing_event", log)

    await ua.aggregate_daily_usage(date(2026, 7, 18))

    assert log.await_args.kwargs["metadata"]["overage_minutes"] == 0.0


async def test_no_tenants_with_calls(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(ua, "get_pool", lambda: pool)
    conn.fetch.return_value = []
    log = AsyncMock()
    monkeypatch.setattr(ua, "log_billing_event", log)

    assert await ua.aggregate_daily_usage(date(2026, 7, 18)) == 0
    log.assert_not_awaited()
