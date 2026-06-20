"""Consent disclosure read for the portal settings page (ticket 5.14)."""

from __future__ import annotations

from uuid import UUID

from app.db.pool import get_pool
from app.models.portal import ConsentDisclosure
from app.webhooks.twilio_twiml import CONSENT_DISCLOSURE_TEXT, effective_disclosure


async def get_consent_disclosure(tenant_id: UUID) -> ConsentDisclosure:
    """Return the disclosure spoken on this tenant's calls: their override if
    set, otherwise the standard line."""

    pool = get_pool()
    async with pool.acquire() as conn:
        override = await conn.fetchval(
            "SELECT consent_disclosure_text FROM tenants WHERE id = $1", tenant_id
        )

    return ConsentDisclosure(
        text=effective_disclosure(override),
        is_custom=bool(override and override.strip()),
        default_text=CONSENT_DISCLOSURE_TEXT,
    )
