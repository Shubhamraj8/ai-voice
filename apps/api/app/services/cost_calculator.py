"""Per-call cost calculation (ticket 4.14).

Computes COGS from the call's duration, summed per-turn ``tts_chars``, and the
``provider_snapshot`` (which providers actually ran), then persists the four
components + total on ``calls``. Run at post-call time alongside the summary job.

Rates are USD and documented inline — verify against current provider pricing.
"""

from __future__ import annotations

import json
from uuid import UUID

import structlog

from app.db.pool import get_pool

logger = structlog.get_logger(__name__)

# --- provider rates (verify against live pricing) ----------------------------
DEEPGRAM_STT_PER_MIN = 0.0048  # Nova-3 Monolingual
DEEPGRAM_TTS_PER_1K_CHARS = 0.015  # Aura-1
TWILIO_INDIA_INBOUND_PER_MIN = 0.0085
# DeepSeek V4 Flash blended estimate. We don't yet track per-call tokens, so LLM
# cost is ESTIMATED from transcript length; refine once token usage is captured.
DEEPSEEK_PER_1K_TOKENS = 0.0003
CHARS_PER_TOKEN = 4


def stt_cost(provider: str | None, duration_secs: int | None) -> float:
    if provider == "deepgram" and duration_secs:
        return duration_secs / 60 * DEEPGRAM_STT_PER_MIN
    return 0.0


def tts_cost(provider: str | None, tts_chars: int | None) -> float:
    if provider == "deepgram" and tts_chars:
        return tts_chars / 1000 * DEEPGRAM_TTS_PER_1K_CHARS
    return 0.0


def telephony_cost(duration_secs: int | None) -> float:
    if duration_secs:
        return duration_secs / 60 * TWILIO_INDIA_INBOUND_PER_MIN
    return 0.0


def llm_cost(provider: str | None, transcript_chars: int | None) -> float:
    """Estimate from transcript length until per-call token usage is tracked."""

    if provider and provider.startswith("deepseek") and transcript_chars:
        est_tokens = transcript_chars / CHARS_PER_TOKEN
        return est_tokens / 1000 * DEEPSEEK_PER_1K_TOKENS
    return 0.0


def _snapshot(raw) -> dict:
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except (TypeError, ValueError):
            return {}
    return raw or {}


async def compute_and_store_cost(call_id: UUID) -> None:
    """Compute the four cost components + total and write them to ``calls``.
    Idempotent (UPDATE), best-effort."""

    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            call = await conn.fetchrow(
                "SELECT duration_secs, provider_snapshot FROM calls WHERE id = $1",
                call_id,
            )
            if call is None:
                return
            tts_chars = await conn.fetchval(
                "SELECT COALESCE(SUM(tts_chars), 0) FROM call_messages "
                "WHERE call_id = $1",
                call_id,
            )
            transcript_chars = await conn.fetchval(
                "SELECT COALESCE(SUM(length(content)), 0) FROM call_messages "
                "WHERE call_id = $1 AND role IN ('user', 'assistant')",
                call_id,
            )

        snapshot = _snapshot(call["provider_snapshot"])
        duration = call["duration_secs"]

        c_stt = stt_cost(snapshot.get("stt"), duration)
        c_tts = tts_cost(snapshot.get("tts"), tts_chars)
        c_llm = llm_cost(snapshot.get("llm"), transcript_chars)
        c_tel = telephony_cost(duration)
        total = c_stt + c_tts + c_llm + c_tel

        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE calls SET cost_stt_usd = $2, cost_tts_usd = $3, "
                "cost_llm_usd = $4, cost_telephony_usd = $5, cost_total_usd = $6, "
                "cost_usd = $6 WHERE id = $1",
                call_id,
                round(c_stt, 5),
                round(c_tts, 5),
                round(c_llm, 5),
                round(c_tel, 5),
                round(total, 5),
            )
        logger.info("cost_computed", call_id=str(call_id), total=round(total, 5))
    except Exception as exc:
        logger.error("cost_calc_failed", call_id=str(call_id), error=str(exc))
