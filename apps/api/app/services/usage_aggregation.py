"""Daily usage rollup (ticket 5.06).

Provider-agnostic: sums each active tenant's previous-day call minutes + cost
from ``calls`` and records one ``usage_reported`` row in ``billing_events`` per
tenant per day (with month-to-date minutes vs the plan's included minutes for
overage). Powers the portal usage card (5.11) and manual invoicing. No external
usage push. Idempotent: re-running for a day replaces that day's rows.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime, time, timedelta

import structlog

from app.db.pool import get_pool
from app.services.billing import log_billing_event

logger = structlog.get_logger(__name__)

# Re-runs are idempotent, so a few times a day is safe and resilient to restarts.
USAGE_INTERVAL_SECONDS = 21600  # 6 hours

_AGG_QUERY = """
WITH day_usage AS (
    SELECT tenant_id,
           SUM(duration_secs) / 60.0 AS day_minutes,
           COALESCE(SUM(cost_total_usd), 0) AS day_cost
    FROM calls
    WHERE started_at >= $1 AND started_at < $2
    GROUP BY tenant_id
),
month_usage AS (
    SELECT tenant_id, SUM(duration_secs) / 60.0 AS month_minutes
    FROM calls
    WHERE started_at >= $3 AND started_at < $2
    GROUP BY tenant_id
)
SELECT t.id AS tenant_id,
       COALESCE(d.day_minutes, 0) AS day_minutes,
       COALESCE(d.day_cost, 0) AS day_cost,
       COALESCE(m.month_minutes, 0) AS month_minutes,
       COALESCE(p.included_minutes, 0) AS included_minutes
FROM tenants t
JOIN day_usage d ON d.tenant_id = t.id
LEFT JOIN month_usage m ON m.tenant_id = t.id
LEFT JOIN pricing_plans p ON p.key = t.plan
WHERE t.status = 'active'
"""


async def aggregate_daily_usage(target_day: date) -> int:
    """Roll up usage for ``target_day`` into billing_events. Returns tenant count."""

    day_start = datetime.combine(target_day, time.min, tzinfo=UTC)
    day_end = day_start + timedelta(days=1)
    month_start = datetime.combine(target_day.replace(day=1), time.min, tzinfo=UTC)

    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(_AGG_QUERY, day_start, day_end, month_start)
            for row in rows:
                month_minutes = float(row["month_minutes"] or 0)
                overage = max(0.0, month_minutes - row["included_minutes"])
                async with conn.transaction():
                    await conn.execute(
                        "DELETE FROM billing_events WHERE tenant_id = $1 "
                        "AND event_type = 'usage_reported' "
                        "AND metadata_json->>'date' = $2",
                        row["tenant_id"],
                        target_day.isoformat(),
                    )
                    await log_billing_event(
                        conn,
                        tenant_id=row["tenant_id"],
                        event_type="usage_reported",
                        units=round(float(row["day_minutes"] or 0), 4),
                        metadata={
                            "date": target_day.isoformat(),
                            "day_minutes": round(float(row["day_minutes"] or 0), 2),
                            "month_minutes": round(month_minutes, 2),
                            "overage_minutes": round(overage, 2),
                            "day_cost_usd": round(float(row["day_cost"] or 0), 5),
                        },
                    )
    except Exception as exc:
        logger.error("usage_aggregation_failed", error=str(exc))
        return 0

    if rows:
        logger.info("usage_aggregated", day=target_day.isoformat(), tenants=len(rows))
    return len(rows)


async def run_usage_aggregation(
    *, interval_seconds: int = USAGE_INTERVAL_SECONDS
) -> None:
    """Loop forever rolling up the previous day's usage; cancel to stop."""

    logger.info("usage_aggregation_started", interval_seconds=interval_seconds)
    try:
        while True:
            await asyncio.sleep(interval_seconds)
            yesterday = (datetime.now(UTC) - timedelta(days=1)).date()
            await aggregate_daily_usage(yesterday)
    except asyncio.CancelledError:
        logger.info("usage_aggregation_stopped")
        raise
