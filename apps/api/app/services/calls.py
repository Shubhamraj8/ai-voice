"""Call lifecycle persistence (ticket 2.13).

Writes one ``calls`` row per phone call and one ``call_messages`` row per turn,
and closes calls on the Twilio status callback (or via the stale-call reaper if
the callback never arrives).

Every write is best-effort: a database failure (including an uninitialised pool)
is logged and swallowed so it never drops the live call.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from uuid import UUID

import structlog

from app.db.pool import get_pool

if TYPE_CHECKING:
    from app.config import Settings

logger = structlog.get_logger(__name__)


# Hardcoded for now — seeded by migration 010_seed_dev_tenant_agent.
# Real per-call tenant/agent lookup arrives with ticket 3.09.
DEV_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")
DEV_AGENT_ID = UUID("00000000-0000-0000-0000-000000000002")


def build_provider_snapshot(settings: Settings) -> dict[str, str | None]:
    """Record which providers a call used, mirroring the pipeline branch logic.

    The pipeline runs the full STT→LLM→TTS path only when both Deepgram and
    DeepSeek keys are present; with just Deepgram it runs STT+TTS (no LLM).
    """

    has_deepgram = bool(settings.deepgram_api_key)
    has_deepseek = bool(settings.deepseek_api_key)

    return {
        "stt": "deepgram" if has_deepgram else None,
        "tts": "deepgram" if has_deepgram else None,
        "llm": "deepseek_native" if (has_deepgram and has_deepseek) else None,
    }


async def start_call(
    *,
    twilio_call_sid: str,
    from_number: str,
    provider_snapshot: dict[str, str | None],
    tenant_id: UUID = DEV_TENANT_ID,
    agent_id: UUID = DEV_AGENT_ID,
) -> UUID | None:
    """Insert the ``calls`` row for a new call; return its id (idempotent).

    Twilio may retry the voice webhook, so a duplicate ``twilio_call_sid`` is
    treated as the same call and the existing id is returned.
    """

    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            call_id = await conn.fetchval(
                """
                INSERT INTO calls (
                    tenant_id, agent_id, twilio_call_sid,
                    from_number, provider_snapshot
                )
                VALUES ($1, $2, $3, $4, $5::jsonb)
                ON CONFLICT (twilio_call_sid)
                DO UPDATE SET twilio_call_sid = EXCLUDED.twilio_call_sid
                RETURNING id
                """,
                tenant_id,
                agent_id,
                twilio_call_sid,
                from_number,
                json.dumps(provider_snapshot),
            )
        logger.info(
            "call_started",
            call_id=str(call_id),
            twilio_call_sid=twilio_call_sid,
        )
        return call_id
    except Exception as exc:
        logger.error(
            "call_start_failed",
            error=str(exc),
            twilio_call_sid=twilio_call_sid,
        )
        return None


async def get_call_id_by_sid(twilio_call_sid: str) -> UUID | None:
    """Look up our internal call id from a Twilio CallSid."""

    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            return await conn.fetchval(
                "SELECT id FROM calls WHERE twilio_call_sid = $1",
                twilio_call_sid,
            )
    except Exception as exc:
        logger.error(
            "call_lookup_failed",
            error=str(exc),
            twilio_call_sid=twilio_call_sid,
        )
        return None


async def record_turn(
    *,
    call_id: UUID,
    role: str,
    content: str,
    tenant_id: UUID | None = None,
    latency_ms: int | None = None,
    tts_chars: int | None = None,
) -> None:
    """Insert one ``call_messages`` row for a completed turn."""

    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO call_messages (
                    call_id, tenant_id, role, content, latency_ms, tts_chars
                )
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                call_id,
                tenant_id or DEV_TENANT_ID,
                role,
                content,
                latency_ms,
                tts_chars,
            )
    except Exception as exc:
        logger.error(
            "call_turn_record_failed",
            error=str(exc),
            call_id=str(call_id),
            role=role,
        )


async def end_call(
    *,
    twilio_call_sid: str,
    duration_secs: int | None = None,
) -> UUID | None:
    """Close a call: set ``ended_at`` and ``duration_secs``.

    Only the first close wins (``ended_at IS NULL`` guard), so a late status
    callback after the reaper already closed the call is a no-op. Falls back to
    a computed duration when Twilio does not supply ``CallDuration``.
    """

    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            call_id = await conn.fetchval(
                """
                UPDATE calls
                SET ended_at = now(),
                    duration_secs = COALESCE(
                        $2, EXTRACT(EPOCH FROM (now() - started_at))::int
                    )
                WHERE twilio_call_sid = $1 AND ended_at IS NULL
                RETURNING id
                """,
                twilio_call_sid,
                duration_secs,
            )
        if call_id is not None:
            logger.info(
                "call_ended",
                call_id=str(call_id),
                twilio_call_sid=twilio_call_sid,
                duration_secs=duration_secs,
            )
        return call_id
    except Exception as exc:
        logger.error(
            "call_end_failed",
            error=str(exc),
            twilio_call_sid=twilio_call_sid,
        )
        return None


async def set_recording_url(*, twilio_call_sid: str, path: str) -> None:
    """Store the Supabase Storage path of a call's recording (ticket 2.14)."""

    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE calls SET recording_url = $2 WHERE twilio_call_sid = $1",
                twilio_call_sid,
                path,
            )
        logger.info(
            "call_recording_url_set",
            twilio_call_sid=twilio_call_sid,
            path=path,
        )
    except Exception as exc:
        logger.error(
            "call_recording_url_failed",
            error=str(exc),
            twilio_call_sid=twilio_call_sid,
        )


async def close_stale_calls(*, max_age_seconds: int) -> int:
    """Close calls left open past ``max_age_seconds`` (dropped before callback).

    Returns the number of calls closed.
    """

    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                UPDATE calls
                SET ended_at = now(),
                    duration_secs = EXTRACT(EPOCH FROM (now() - started_at))::int
                WHERE ended_at IS NULL
                  AND started_at < now() - make_interval(secs => $1)
                RETURNING id
                """,
                max_age_seconds,
            )
        if rows:
            logger.info("stale_calls_closed", count=len(rows))
        return len(rows)
    except Exception as exc:
        logger.error("stale_call_close_failed", error=str(exc))
        return 0
