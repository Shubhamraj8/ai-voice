"""Platform-wide KPI counts for the internal metrics page."""

from __future__ import annotations

from app.db.pool import get_pool


async def platform_metrics() -> dict:
    """Tenant + call counts across the whole platform."""

    pool = get_pool()
    async with pool.acquire() as conn:
        tenants = await conn.fetchrow("""
            SELECT COUNT(*) AS total,
                   COUNT(*) FILTER (WHERE status = 'active') AS active,
                   COUNT(*) FILTER (WHERE status = 'paused') AS paused,
                   COUNT(*) FILTER (WHERE status = 'churned') AS churned
            FROM tenants
            WHERE deleted_at IS NULL
            """)
        calls = await conn.fetchrow("""
            SELECT COUNT(*) AS total,
                   COUNT(*) FILTER (
                       WHERE started_at >= now() - interval '24 hours'
                   ) AS last_24h,
                   COALESCE(SUM(duration_secs), 0) / 60.0 AS minutes
            FROM calls
            """)

    return {
        "tenants": {
            "total": tenants["total"],
            "active": tenants["active"],
            "paused": tenants["paused"],
            "churned": tenants["churned"],
        },
        "calls": {"total": calls["total"], "last_24h": calls["last_24h"]},
        "minutes_total": round(float(calls["minutes"] or 0), 1),
    }
