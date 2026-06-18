"""Tenant access-window expiry (ticket 5.03).

A tenant's agents answer only while ``now() < paid_until``. This periodic job
pauses any active tenant whose paid window has lapsed; call routing already gates
on ``status = 'active'``, so paused tenants stop answering immediately. Recording
a payment (5.05) — or extending ``paid_until`` — re-activates them.
"""

from __future__ import annotations

import asyncio

import structlog

from app.db.pool import get_pool
from app.services.audit import log_system_action

logger = structlog.get_logger(__name__)

EXPIRY_INTERVAL_SECONDS = 300


async def expire_lapsed_tenants() -> int:
    """Pause active tenants whose ``paid_until`` has passed. Returns the count."""

    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                UPDATE tenants
                SET status = 'paused', updated_at = now()
                WHERE status = 'active'
                  AND paid_until IS NOT NULL
                  AND paid_until < now()
                RETURNING id
                """)
    except Exception as exc:
        logger.error("tenant_expiry_failed", error=str(exc))
        return 0

    for row in rows:
        await log_system_action(
            action="tenant.access_expired",
            tenant_id=row["id"],
            target_type="tenant",
            target_id=row["id"],
        )
    if rows:
        logger.info("tenants_expired", count=len(rows))
    return len(rows)


async def run_subscription_expiry(
    *, interval_seconds: int = EXPIRY_INTERVAL_SECONDS
) -> None:
    """Loop forever pausing lapsed tenants; cancel the task to stop it."""

    logger.info("subscription_expiry_started", interval_seconds=interval_seconds)
    try:
        while True:
            await asyncio.sleep(interval_seconds)
            await expire_lapsed_tenants()
    except asyncio.CancelledError:
        logger.info("subscription_expiry_stopped")
        raise
