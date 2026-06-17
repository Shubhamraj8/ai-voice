"""SMS persistence + lookups for the sendSms tool (ticket 4.09)."""

from __future__ import annotations

from uuid import UUID

import structlog

from app.db.pool import get_pool

logger = structlog.get_logger(__name__)

# Single-segment-ish cap we truncate to; well under Twilio's 1600 hard cap.
MAX_SMS_CHARS = 320


def truncate_sms(body: str) -> str:
    """Trim to MAX_SMS_CHARS, marking truncation with an ellipsis."""

    body = body.strip()
    if len(body) <= MAX_SMS_CHARS:
        return body
    return body[: MAX_SMS_CHARS - 1].rstrip() + "…"


async def get_agent_from_number(agent_id: UUID | None) -> str | None:
    """The agent's own Twilio number — the only number it may send from."""

    if agent_id is None:
        return None
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT phone_number FROM agents WHERE id = $1", agent_id
        )
    return row["phone_number"] if row else None


async def get_caller_number(call_id: UUID | None) -> str | None:
    """The inbound caller's number (default SMS recipient)."""

    if call_id is None:
        return None
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT from_number FROM calls WHERE id = $1", call_id
        )
    return row["from_number"] if row else None


async def log_sms(
    *,
    tenant_id: UUID | None,
    call_id: UUID | None,
    to_number: str,
    body: str,
    twilio_sid: str | None,
    status: str,
    error: str | None = None,
) -> None:
    """Insert an ``sms_log`` row. Best-effort."""

    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO sms_log (
                    tenant_id, call_id, to_number, body, twilio_sid, status, error
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                tenant_id,
                call_id,
                to_number,
                body,
                twilio_sid,
                status,
                error,
            )
    except Exception as exc:
        logger.error("sms_log_insert_failed", error=str(exc))


async def update_sms_status(
    twilio_sid: str, status: str, *, error: str | None = None
) -> None:
    """Backfill delivery status from the Twilio status webhook. Best-effort."""

    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE sms_log SET status = $2, error = $3 WHERE twilio_sid = $1",
                twilio_sid,
                status,
                error,
            )
    except Exception as exc:
        logger.error("sms_status_update_failed", error=str(exc), twilio_sid=twilio_sid)
