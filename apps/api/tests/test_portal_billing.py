"""Tests for the portal billing summary (ticket 5.11). DB mocked."""

import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from app.services import portal_billing as pb


def _tenant(paid_until, *, plan="starter", status="active"):
    return SimpleNamespace(
        id=uuid.uuid4(), plan=plan, paid_until=paid_until, status=status
    )


async def test_billing_summary_active_with_overage(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(pb, "get_pool", lambda: pool)
    conn.fetchval.return_value = 360.0  # minutes used this cycle
    conn.fetchrow.return_value = {"name": "Starter", "included_minutes": 300}

    summary = await pb.get_billing_summary(
        _tenant(datetime.now(UTC) + timedelta(days=30))
    )

    assert summary.usage.minutes_used == 360.0
    assert summary.usage.included_minutes == 300
    assert summary.usage.overage_minutes == 60.0
    # projection is run-rate; always >= what's already used
    assert summary.usage.projected_minutes >= summary.usage.minutes_used
    assert summary.plan.name == "Starter"
    assert summary.access.expiry_state == "active"
    assert (
        summary.access.days_remaining is not None and summary.access.days_remaining > 7
    )


async def test_billing_summary_expiring_soon(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(pb, "get_pool", lambda: pool)
    conn.fetchval.return_value = 0
    conn.fetchrow.return_value = {"name": "Starter", "included_minutes": 300}

    summary = await pb.get_billing_summary(
        _tenant(datetime.now(UTC) + timedelta(days=3))
    )

    assert summary.access.expiry_state == "expiring_soon"
    assert summary.usage.overage_minutes == 0.0


async def test_billing_summary_expired(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(pb, "get_pool", lambda: pool)
    conn.fetchval.return_value = 10
    conn.fetchrow.return_value = {"name": "Starter", "included_minutes": 300}

    summary = await pb.get_billing_summary(
        _tenant(datetime.now(UTC) - timedelta(days=2))
    )

    assert summary.access.expiry_state == "expired"


async def test_billing_summary_no_access_window(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(pb, "get_pool", lambda: pool)
    conn.fetchval.return_value = 0
    conn.fetchrow.return_value = None  # no matching pricing plan

    summary = await pb.get_billing_summary(_tenant(None, plan="custom"))

    assert summary.access.expiry_state == "none"
    assert summary.access.days_remaining is None
    assert summary.plan.included_minutes == 0
