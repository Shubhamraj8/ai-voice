"""Portal dashboard summary (ticket 5.08).

One round-trip's worth of aggregates for the tenant overview page: month-to-date
stats, a 14-day calls series, the 5 newest calls, knowledge status, and the plan
card. Aggregations use UTC month/day boundaries to match the billing rollup
(5.06) so the numbers reconcile with the usage card (5.11).
"""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta

import structlog

from app.db.pool import get_pool
from app.models.portal import (
    CallPoint,
    DashboardStats,
    DashboardSummary,
    KnowledgeStatus,
    PlanCard,
    RecentCall,
)
from app.models.tenant import Tenant

logger = structlog.get_logger(__name__)

CHART_DAYS = 14
RECENT_CALLS_LIMIT = 5


async def get_dashboard_summary(tenant: Tenant) -> DashboardSummary:
    now = datetime.now(UTC)
    today = now.date()
    month_start = datetime(now.year, now.month, 1, tzinfo=UTC)
    window_start_date = today - timedelta(days=CHART_DAYS - 1)
    window_start = datetime.combine(window_start_date, time.min, tzinfo=UTC)

    pool = get_pool()
    async with pool.acquire() as conn:
        month = await conn.fetchrow(
            """
            SELECT COUNT(*) AS calls,
                   COALESCE(SUM(duration_secs), 0) / 60.0 AS minutes
            FROM calls
            WHERE tenant_id = $1 AND started_at >= $2
            """,
            tenant.id,
            month_start,
        )
        escalations = await conn.fetchval(
            "SELECT COUNT(*) FROM escalations "
            "WHERE tenant_id = $1 AND created_at >= $2",
            tenant.id,
            month_start,
        )
        series_rows = await conn.fetch(
            """
            SELECT (started_at AT TIME ZONE 'UTC')::date AS day, COUNT(*) AS count
            FROM calls
            WHERE tenant_id = $1 AND started_at >= $2
            GROUP BY day
            """,
            tenant.id,
            window_start,
        )
        recent_rows = await conn.fetch(
            """
            SELECT id, from_number, started_at, duration_secs,
                   outcome, intent, summary
            FROM calls
            WHERE tenant_id = $1
            ORDER BY started_at DESC
            LIMIT $2
            """,
            tenant.id,
            RECENT_CALLS_LIMIT,
        )
        knowledge = await conn.fetchrow(
            """
            SELECT COUNT(*) AS documents,
                   COUNT(*) FILTER (WHERE status = 'ready') AS ready,
                   MAX(uploaded_at) AS last_upload
            FROM knowledge_documents
            WHERE tenant_id = $1
            """,
            tenant.id,
        )
        plan_row = await conn.fetchrow(
            "SELECT name, included_minutes FROM pricing_plans WHERE key = $1",
            tenant.plan,
        )

    # Fill missing days with 0 so the chart is a contiguous 14-day window.
    counts = {row["day"]: row["count"] for row in series_rows}
    calls_over_time = [
        CallPoint(
            date=window_start_date + timedelta(days=i),
            count=counts.get(window_start_date + timedelta(days=i), 0),
        )
        for i in range(CHART_DAYS)
    ]

    included_minutes = int(plan_row["included_minutes"]) if plan_row else 0

    return DashboardSummary(
        stats=DashboardStats(
            calls_this_month=month["calls"] or 0,
            minutes_used=round(float(month["minutes"] or 0), 1),
            minutes_included=included_minutes,
            escalations_this_month=escalations or 0,
        ),
        calls_over_time=calls_over_time,
        recent_calls=[RecentCall(**dict(row)) for row in recent_rows],
        knowledge=KnowledgeStatus(
            document_count=knowledge["documents"] or 0,
            ready_count=knowledge["ready"] or 0,
            last_upload=knowledge["last_upload"],
        ),
        plan=PlanCard(
            key=tenant.plan,
            name=plan_row["name"] if plan_row else None,
            included_minutes=included_minutes,
            paid_until=tenant.paid_until,
        ),
    )
