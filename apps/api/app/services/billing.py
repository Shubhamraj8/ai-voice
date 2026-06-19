"""Billing ledger — manual payments + access extension (ticket 5.05).

No payment gateway in v1: the team records offline payments, which write a
``billing_events`` row and extend the tenant's ``paid_until`` (re-activating a
paused tenant). ``log_billing_event`` is shared with the usage rollup (5.06).
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, time
from uuid import UUID

import structlog

from app.db.pool import get_pool
from app.errors import api_error
from app.models.billing import BillingEvent

logger = structlog.get_logger(__name__)


def _to_billing_event(row) -> BillingEvent:
    """Map a billing_events row to the API model (jsonb arrives as a string)."""

    data = dict(row)
    meta = data.pop("metadata_json", None)
    if isinstance(meta, str):
        meta = json.loads(meta)
    data["metadata"] = meta
    return BillingEvent.model_validate(data)


async def list_billing_events(
    tenant_id: UUID, *, event_type: str | None = None, limit: int = 100
) -> list[BillingEvent]:
    """Read a tenant's ledger, newest first. Used by the portal billing page
    (5.11) and the internal billing view; scoping is by ``tenant_id``."""

    pool = get_pool()
    async with pool.acquire() as conn:
        if event_type:
            rows = await conn.fetch(
                "SELECT * FROM billing_events WHERE tenant_id = $1 "
                "AND event_type = $2 ORDER BY created_at DESC LIMIT $3",
                tenant_id,
                event_type,
                limit,
            )
        else:
            rows = await conn.fetch(
                "SELECT * FROM billing_events WHERE tenant_id = $1 "
                "ORDER BY created_at DESC LIMIT $2",
                tenant_id,
                limit,
            )
    return [_to_billing_event(row) for row in rows]


async def log_billing_event(
    conn,
    *,
    tenant_id: UUID,
    event_type: str,
    units: float | None = None,
    amount_inr: float | None = None,
    call_id: UUID | None = None,
    metadata: dict | None = None,
) -> None:
    """Insert one ``billing_events`` row (composable inside a transaction)."""

    await conn.execute(
        """
        INSERT INTO billing_events (
            tenant_id, call_id, event_type, units, amount_inr, metadata_json
        )
        VALUES ($1, $2, $3, $4, $5, $6::jsonb)
        """,
        tenant_id,
        call_id,
        event_type,
        units,
        amount_inr,
        json.dumps(metadata) if metadata is not None else None,
    )


async def record_payment(
    tenant_id: UUID,
    *,
    amount_inr: float,
    method: str,
    plan: str,
    period_start: date,
    period_end: date,
    reference: str | None = None,
) -> dict:
    """Record an offline payment: log it, extend ``paid_until`` to the end of the
    paid period, and re-activate the tenant. Returns the new access window."""

    # Access lasts through the end of the paid-through day.
    paid_until = datetime.combine(period_end, time.max).replace(tzinfo=UTC)

    pool = get_pool()
    async with pool.acquire() as conn:
        tenant = await conn.fetchrow("SELECT id FROM tenants WHERE id = $1", tenant_id)
        if tenant is None:
            raise api_error(404, "tenant_not_found", "Tenant not found")

        async with conn.transaction():
            await log_billing_event(
                conn,
                tenant_id=tenant_id,
                event_type="payment_recorded",
                amount_inr=amount_inr,
                metadata={
                    "method": method,
                    "plan": plan,
                    "period_start": period_start.isoformat(),
                    "period_end": period_end.isoformat(),
                    "reference": reference,
                },
            )
            await conn.execute(
                "UPDATE tenants "
                "SET paid_until = $2, status = 'active', archived_at = NULL, "
                "updated_at = now() WHERE id = $1",
                tenant_id,
                paid_until,
            )

    logger.info(
        "payment_recorded",
        tenant_id=str(tenant_id),
        amount_inr=amount_inr,
        paid_until=paid_until.isoformat(),
    )
    return {"status": "recorded", "paid_until": paid_until.isoformat()}
