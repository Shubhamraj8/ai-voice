"""Per-tenant inbound call routing (ticket 3.09).

Resolves the Twilio ``To`` number to the owning tenant + agent so the hardcoded
dev identifiers can be dropped. Only active agents on active tenants resolve;
soft-deleted agents (``archived_at``) do not, even if the number is still on
Twilio.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

import structlog

from app.db.pool import get_pool

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class ResolvedRoute:
    tenant_id: UUID
    agent_id: UUID
    stt: str
    tts: str
    llm: str


async def resolve_agent_by_number(to_number: str) -> ResolvedRoute | None:
    """Return the active tenant+agent owning ``to_number`` (with the tenant's
    provider_config), or None."""

    if not to_number:
        return None

    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT a.id AS agent_id, a.tenant_id,
                       t.provider_config->>'stt' AS stt,
                       t.provider_config->>'tts' AS tts,
                       t.provider_config->>'llm' AS llm
                FROM agents a
                JOIN tenants t ON t.id = a.tenant_id
                WHERE a.phone_number = $1
                  AND a.is_active = true
                  AND a.archived_at IS NULL
                  AND t.archived_at IS NULL
                  AND t.status = 'active'
                LIMIT 1
                """,
                to_number,
            )
    except Exception as exc:
        logger.error("agent_resolution_failed", error=str(exc), to_number=to_number)
        return None

    if row is None:
        return None
    return ResolvedRoute(
        tenant_id=row["tenant_id"],
        agent_id=row["agent_id"],
        stt=row["stt"],
        tts=row["tts"],
        llm=row["llm"],
    )
