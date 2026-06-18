"""Lead capture + team notification (ticket 5.02)."""

from __future__ import annotations

from uuid import UUID

import structlog

from app.config import get_settings
from app.db.pool import get_pool
from app.errors import api_error
from app.models.leads import Lead, LeadCreate
from app.services.email import send_email

logger = structlog.get_logger(__name__)


async def create_lead(body: LeadCreate) -> Lead:
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO leads (
                business_name, contact_name, contact_email,
                contact_phone, message, source
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING *
            """,
            body.business_name,
            body.contact_name,
            body.contact_email,
            body.contact_phone,
            body.message,
            body.source,
        )
    logger.info("lead_created", lead_id=str(row["id"]), source=body.source)
    return Lead.model_validate(dict(row))


async def list_leads(*, status: str | None = None, limit: int = 100) -> list[Lead]:
    pool = get_pool()
    async with pool.acquire() as conn:
        if status:
            rows = await conn.fetch(
                "SELECT * FROM leads WHERE status = $1 "
                "ORDER BY created_at DESC LIMIT $2",
                status,
                limit,
            )
        else:
            rows = await conn.fetch(
                "SELECT * FROM leads ORDER BY created_at DESC LIMIT $1", limit
            )
    return [Lead.model_validate(dict(row)) for row in rows]


async def update_lead_status(lead_id: UUID, status: str) -> Lead:
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "UPDATE leads SET status = $2 WHERE id = $1 RETURNING *", lead_id, status
        )
    if row is None:
        raise api_error(404, "lead_not_found", "Lead not found")
    return Lead.model_validate(dict(row))


async def notify_team_of_lead(lead: Lead) -> None:
    """Email the configured team inbox about a new lead. Best-effort + guarded:
    no-op when ``LEADS_NOTIFY_EMAIL`` is unset."""

    to = get_settings().leads_notify_email
    if not to:
        logger.info("lead_notify_skipped_no_inbox", lead_id=str(lead.id))
        return

    html = (
        "<h2>New lead</h2>"
        f"<p><strong>Business:</strong> {lead.business_name or '—'}</p>"
        f"<p><strong>Name:</strong> {lead.contact_name or '—'}</p>"
        f"<p><strong>Email:</strong> {lead.contact_email}</p>"
        f"<p><strong>Phone:</strong> {lead.contact_phone or '—'}</p>"
        f"<p><strong>Source:</strong> {lead.source or '—'}</p>"
        f"<p><strong>Message:</strong> {lead.message or '—'}</p>"
    )
    await send_email(
        to=to,
        subject=f"New lead — {lead.business_name or lead.contact_email}",
        html=html,
    )
