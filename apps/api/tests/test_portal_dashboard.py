"""Tests for the portal dashboard summary (ticket 5.08). DB mocked."""

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

from app.services import portal_dashboard as pd


async def test_dashboard_summary(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(pd, "get_pool", lambda: pool)
    tenant = SimpleNamespace(
        id=uuid.uuid4(), plan="starter", paid_until=datetime(2026, 8, 1, tzinfo=UTC)
    )
    today = datetime.now(UTC).date()

    conn.fetchrow.side_effect = [
        {"calls": 12, "minutes": 84.5},  # month
        {
            "documents": 3,
            "ready": 2,
            "last_upload": datetime(2026, 6, 1, tzinfo=UTC),
        },  # knowledge
        {"name": "Starter", "included_minutes": 300},  # plan
    ]
    conn.fetchval.return_value = 4  # escalations this month
    conn.fetch.side_effect = [
        [{"day": today, "count": 5}],  # 14-day series
        [
            {  # recent calls
                "id": uuid.uuid4(),
                "from_number": "+919876543210",
                "started_at": datetime(2026, 6, 18, tzinfo=UTC),
                "duration_secs": 120,
                "outcome": "booked",
                "intent": "appointment",
                "summary": "Booked a slot",
            }
        ],
    ]

    summary = await pd.get_dashboard_summary(tenant)

    assert summary.stats.calls_this_month == 12
    assert summary.stats.minutes_used == 84.5
    assert summary.stats.minutes_included == 300
    assert summary.stats.escalations_this_month == 4
    # contiguous 14-day window; today's bucket filled from the series, gaps zeroed
    assert len(summary.calls_over_time) == 14
    assert summary.calls_over_time[-1].date == today
    assert summary.calls_over_time[-1].count == 5
    assert summary.calls_over_time[0].count == 0
    assert len(summary.recent_calls) == 1
    assert summary.recent_calls[0].from_number == "+919876543210"
    assert summary.knowledge.document_count == 3
    assert summary.knowledge.ready_count == 2
    assert summary.plan.name == "Starter"
    assert summary.plan.paid_until == tenant.paid_until


async def test_dashboard_summary_empty_tenant(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(pd, "get_pool", lambda: pool)
    tenant = SimpleNamespace(id=uuid.uuid4(), plan="custom", paid_until=None)

    conn.fetchrow.side_effect = [
        {"calls": 0, "minutes": 0},
        {"documents": 0, "ready": 0, "last_upload": None},
        None,  # no matching pricing plan
    ]
    conn.fetchval.return_value = 0
    conn.fetch.side_effect = [[], []]

    summary = await pd.get_dashboard_summary(tenant)

    assert summary.stats.calls_this_month == 0
    assert summary.stats.minutes_included == 0
    assert summary.plan.name is None
    assert summary.recent_calls == []
    assert all(p.count == 0 for p in summary.calls_over_time)
