"""Post-call summary job (ticket 4.13).

After a call ends, read its transcript and ask DeepSeek (V4 Flash, OpenAI-
compatible) for a one-paragraph summary, an intent label, and an outcome. Writes
the result to ``calls``. Idempotent (UPDATE), retries once, and on persistent
failure records ``summary = null`` / ``intent = 'unclassified'``. A tool-set
outcome (e.g. 'transferred') is preserved via COALESCE. DeepSeek is guarded:
without a key the job is a no-op.
"""

from __future__ import annotations

import json
from uuid import UUID

import structlog

from app.config import get_settings
from app.db.pool import get_pool

logger = structlog.get_logger(__name__)

VALID_OUTCOMES = {"resolved", "transferred", "escalated", "abandoned", "other"}
SUMMARY_WORD_LIMIT = 80

# Stable system prompt → DeepSeek caches the prefix (cheaper).
SUMMARY_SYSTEM_PROMPT = (
    "You summarise completed phone calls for a business dashboard. Given a "
    "transcript, reply with a JSON object with exactly these keys: "
    '"summary" (one paragraph under 80 words, grounded only in the transcript, '
    "no invented facts), "
    '"intent" (a short label for why the caller called), and '
    '"outcome" (one of: resolved, transferred, escalated, abandoned, other). '
    "Use only information present in the transcript."
)


def _client():
    from openai import AsyncOpenAI

    settings = get_settings()
    if not settings.deepseek_api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is not configured")
    base = settings.deepseek_base_url.rstrip("/")
    if not base.endswith("/v1"):
        base = f"{base}/v1"
    return AsyncOpenAI(api_key=settings.deepseek_api_key, base_url=base)


def _truncate_words(text: str, limit: int = SUMMARY_WORD_LIMIT) -> str:
    words = text.split()
    if len(words) <= limit:
        return text
    return " ".join(words[:limit]) + "…"


async def _build_transcript(call_id: UUID) -> str:
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT role, content FROM call_messages "
            "WHERE call_id = $1 AND role IN ('user', 'assistant') "
            "ORDER BY created_at",
            call_id,
        )
    lines = [
        f"{'Caller' if row['role'] == 'user' else 'Agent'}: {row['content']}"
        for row in rows
    ]
    return "\n".join(lines)


async def _complete_json(transcript: str) -> dict:
    resp = await _client().chat.completions.create(
        model=get_settings().deepseek_model,
        messages=[
            {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": transcript},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)


async def _summarise_with_retry(transcript: str) -> dict | None:
    for attempt in (1, 2):  # one retry
        try:
            return await _complete_json(transcript)
        except Exception as exc:
            logger.warning("summary_attempt_failed", attempt=attempt, error=str(exc))
    return None


async def _write_summary(
    call_id: UUID, *, summary: str | None, intent: str, outcome: str | None
) -> None:
    pool = get_pool()
    async with pool.acquire() as conn:
        # Preserve a tool-set outcome (e.g. 'transferred') via COALESCE.
        await conn.execute(
            "UPDATE calls SET summary = $2, intent = $3, "
            "outcome = COALESCE(outcome, $4), summary_generated_at = now() "
            "WHERE id = $1",
            call_id,
            summary,
            intent,
            outcome,
        )


async def generate_call_summary(call_id: UUID) -> None:
    """Summarise one completed call and persist the result. Best-effort."""

    try:
        transcript = await _build_transcript(call_id)
        if not transcript.strip():
            logger.info("summary_skipped_empty", call_id=str(call_id))
            return

        data = await _summarise_with_retry(transcript)
        if data is None:
            await _write_summary(
                call_id, summary=None, intent="unclassified", outcome=None
            )
            return

        summary = (data.get("summary") or "").strip()
        summary = _truncate_words(summary) if summary else None
        intent = (data.get("intent") or "").strip() or "unclassified"
        outcome = data.get("outcome")
        if outcome not in VALID_OUTCOMES:
            outcome = "other"

        await _write_summary(call_id, summary=summary, intent=intent, outcome=outcome)
        logger.info("summary_generated", call_id=str(call_id), outcome=outcome)
    except Exception as exc:
        logger.error("summary_failed", call_id=str(call_id), error=str(exc))
