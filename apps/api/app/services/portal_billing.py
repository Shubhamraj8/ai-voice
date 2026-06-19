"""Read-only billing summary for the portal (ticket 5.11).

Sources from the calendar-month usage rollup (UTC, matching 5.06),
``pricing_plans`` and ``tenants.paid_until``. Payment history is served
separately by the billing-events read API (5.07)."""

from __future__ import annotations

import calendar
from datetime import UTC, datetime, time, timedelta

import structlog

from app.db.pool import get_pool
from app.models.portal import BillingAccess, BillingSummary, BillingUsage, PlanCard
from app.models.tenant import Tenant

logger = structlog.get_logger(__name__)

EXPIRY_WARN_DAYS = 7


async def get_billing_summary(tenant: Tenant) -> BillingSummary:
    now = datetime.now(UTC)
    today = now.date()
    cycle_start = today.replace(day=1)
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    cycle_end = cycle_start + timedelta(days=days_in_month)  # first of next month
    month_start = datetime.combine(cycle_start, time.min, tzinfo=UTC)

    pool = get_pool()
    async with pool.acquire() as conn:
        minutes_used = await conn.fetchval(
            "SELECT COALESCE(SUM(duration_secs), 0) / 60.0 FROM calls "
            "WHERE tenant_id = $1 AND started_at >= $2",
            tenant.id,
            month_start,
        )
        plan_row = await conn.fetchrow(
            "SELECT name, included_minutes FROM pricing_plans WHERE key = $1",
            tenant.plan,
        )

    minutes_used = round(float(minutes_used or 0), 1)
    included = int(plan_row["included_minutes"]) if plan_row else 0
    overage = round(max(0.0, minutes_used - included), 1)

    # Linear run-rate projection to the end of the calendar-month cycle.
    days_elapsed = (today - cycle_start).days + 1
    projected = round(minutes_used * days_in_month / days_elapsed, 1)

    paid_until = tenant.paid_until
    if paid_until is None:
        expiry_state = "none"
        days_remaining = None
    else:
        days_remaining = (paid_until.date() - today).days
        if paid_until < now:
            expiry_state = "expired"
        elif days_remaining <= EXPIRY_WARN_DAYS:
            expiry_state = "expiring_soon"
        else:
            expiry_state = "active"

    return BillingSummary(
        plan=PlanCard(
            key=tenant.plan,
            name=plan_row["name"] if plan_row else None,
            included_minutes=included,
            paid_until=paid_until,
        ),
        usage=BillingUsage(
            cycle_start=cycle_start,
            cycle_end=cycle_end,
            minutes_used=minutes_used,
            included_minutes=included,
            overage_minutes=overage,
            projected_minutes=projected,
        ),
        access=BillingAccess(
            paid_until=paid_until,
            status=str(tenant.status),
            days_remaining=days_remaining,
            expiry_state=expiry_state,
        ),
    )
