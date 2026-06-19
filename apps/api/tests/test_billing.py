"""Tests for manual payment recording (ticket 5.05). DB mocked."""

import uuid
from datetime import UTC, date, datetime
from unittest.mock import MagicMock

import pytest
from app.services import billing
from fastapi import HTTPException


class _FakeTxn:
    async def __aenter__(self):
        return None

    async def __aexit__(self, *args):
        return False


async def test_record_payment_extends_access(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(billing, "get_pool", lambda: pool)
    conn.fetchrow.return_value = {"id": uuid.uuid4()}
    conn.transaction = MagicMock(return_value=_FakeTxn())

    result = await billing.record_payment(
        uuid.uuid4(),
        amount_inr=2999,
        method="UPI",
        plan="starter",
        period_start=date(2026, 7, 1),
        period_end=date(2026, 7, 31),
        reference="UTR123",
    )

    assert result["status"] == "recorded"
    assert result["paid_until"].startswith("2026-07-31T23:59")
    # one billing_events insert + one tenant UPDATE
    assert conn.execute.await_count == 2
    sqls = " ".join(c.args[0] for c in conn.execute.await_args_list)
    assert "INSERT INTO billing_events" in sqls
    assert "UPDATE tenants" in sqls and "status = 'active'" in sqls


async def test_record_payment_tenant_not_found(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(billing, "get_pool", lambda: pool)
    conn.fetchrow.return_value = None

    with pytest.raises(HTTPException) as exc:
        await billing.record_payment(
            uuid.uuid4(),
            amount_inr=100,
            method="UPI",
            plan="starter",
            period_start=date(2026, 7, 1),
            period_end=date(2026, 7, 31),
        )

    assert exc.value.status_code == 404
    conn.execute.assert_not_awaited()


async def test_list_billing_events_parses_metadata(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(billing, "get_pool", lambda: pool)
    tid = uuid.uuid4()
    conn.fetch.return_value = [
        {
            "id": uuid.uuid4(),
            "tenant_id": tid,
            "call_id": None,
            "event_type": "payment_recorded",
            "units": None,
            "amount_inr": 2999,
            "metadata_json": '{"method": "UPI", "reference": "UTR123"}',
            "created_at": datetime(2026, 7, 1, tzinfo=UTC),
        }
    ]

    events = await billing.list_billing_events(tid)

    assert len(events) == 1
    assert events[0].metadata == {"method": "UPI", "reference": "UTR123"}
    assert events[0].amount_inr == 2999
    # scoped to the requested tenant, no event_type filter applied
    assert conn.fetch.await_args.args[1] == tid


async def test_list_billing_events_event_type_filter(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(billing, "get_pool", lambda: pool)
    tid = uuid.uuid4()
    conn.fetch.return_value = []

    await billing.list_billing_events(tid, event_type="usage_reported", limit=50)

    sql = conn.fetch.await_args.args[0]
    assert "event_type = $2" in sql
    assert conn.fetch.await_args.args[1:] == (tid, "usage_reported", 50)
