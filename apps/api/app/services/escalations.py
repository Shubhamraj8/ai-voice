"""Escalation config lookup + audit log (ticket 4.10)."""

from __future__ import annotations

import json
from uuid import UUID

import structlog

from app.db.pool import get_pool

logger = structlog.get_logger(__name__)


async def get_escalation_config(tenant_id: UUID | None) -> dict | None:
    """Tenant name + owner escalation contacts (email/sms), or None."""

    if tenant_id is None:
        return None
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT business_name, escalation_email, escalation_sms "
            "FROM tenants WHERE id = $1",
            tenant_id,
        )
    return dict(row) if row else None


async def log_escalation(
    *,
    tenant_id: UUID | None,
    call_id: UUID | None,
    summary: str,
    urgency: str,
    email_sent: bool,
    sms_sent: bool,
    payload: dict,
    error: str | None = None,
) -> None:
    """Record an escalation for the audit trail. Best-effort."""

    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO escalations (
                    tenant_id, call_id, summary, urgency,
                    email_sent, sms_sent, payload, error
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8)
                """,
                tenant_id,
                call_id,
                summary,
                urgency,
                email_sent,
                sms_sent,
                json.dumps(payload),
                error,
            )
    except Exception as exc:
        logger.error("escalation_log_failed", error=str(exc))
