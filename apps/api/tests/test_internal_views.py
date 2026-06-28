"""Tests for internal calls + metrics services. DB mocked."""

import uuid
from datetime import UTC, datetime

from app.services import internal_calls as ic
from app.services import internal_metrics as im


def _call_row(**over):
    base = {
        "id": uuid.uuid4(),
        "tenant_id": uuid.uuid4(),
        "tenant_name": "Acme",
        "from_number": "+919876543210",
        "started_at": datetime(2026, 6, 1, tzinfo=UTC),
        "duration_secs": 90,
        "outcome": "booked",
        "intent": "appointment",
    }
    base.update(over)
    return base


async def test_list_all_calls_no_filters(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(ic, "get_pool", lambda: pool)
    conn.fetchval.return_value = 2
    conn.fetch.return_value = [_call_row(), _call_row()]

    total, rows = await ic.list_all_calls(page=1, page_size=25)

    assert total == 2
    assert rows[0]["tenant_name"] == "Acme"
    # rows query gets (page_size, offset) only
    assert conn.fetch.await_args.args[1:] == (25, 0)


async def test_list_all_calls_with_filters(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(ic, "get_pool", lambda: pool)
    conn.fetchval.return_value = 1
    conn.fetch.return_value = [_call_row()]
    tid = uuid.uuid4()

    await ic.list_all_calls(page=2, page_size=10, tenant_id=tid, outcome="booked")

    sql = conn.fetch.await_args.args[0]
    assert "c.tenant_id = $1" in sql and "c.outcome = $2" in sql
    assert conn.fetch.await_args.args[1:] == (tid, "booked", 10, 10)


async def test_platform_metrics(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(im, "get_pool", lambda: pool)
    conn.fetchrow.side_effect = [
        {"total": 10, "active": 7, "paused": 2, "churned": 1},
        {"total": 100, "last_24h": 5, "minutes": 250.5},
    ]

    m = await im.platform_metrics()

    assert m["tenants"] == {"total": 10, "active": 7, "paused": 2, "churned": 1}
    assert m["calls"] == {"total": 100, "last_24h": 5}
    assert m["minutes_total"] == 250.5
