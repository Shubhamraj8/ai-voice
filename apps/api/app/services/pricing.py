"""Pricing plan lookups (ticket 5.01)."""

from __future__ import annotations

import structlog

from app.db.pool import get_pool
from app.models.pricing import PricingPlan

logger = structlog.get_logger(__name__)


async def list_pricing_plans(*, active_only: bool = True) -> list[PricingPlan]:
    """Return pricing plans ordered for display."""

    where = "WHERE active = true" if active_only else ""
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            f"SELECT * FROM pricing_plans {where} ORDER BY sort_order, price_inr_month"
        )
    return [PricingPlan.model_validate(dict(row)) for row in rows]
