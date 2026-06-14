"""Latency percentile metrics for the internal dashboard (ticket 2.15).

Reads per-turn latencies persisted on ``call_messages`` (total in
``latency_ms``, components in ``latency_breakdown``) and reports p50/p95/p99
for each segment over the most recent turns, so bottlenecks can be diagnosed.
"""

from __future__ import annotations

import math

import structlog

from app.db.pool import get_pool

logger = structlog.get_logger(__name__)

# Segment keys reported by the latency endpoint. ``total_ms`` comes from the
# ``latency_ms`` column; the rest from the ``latency_breakdown`` JSONB.
LATENCY_SEGMENTS = ("stt_ms", "llm_ms", "tts_first_byte_ms", "total_ms")
DEFAULT_TURN_LIMIT = 100


def _percentile(values: list[int], pct: float) -> int | None:
    """Linear-interpolated percentile (numpy-style) of integer values."""

    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * (pct / 100)
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return ordered[low]
    interpolated = ordered[low] + (ordered[high] - ordered[low]) * (rank - low)
    return round(interpolated)


def _segment_stats(values: list[int]) -> dict[str, int | None]:
    return {
        "p50": _percentile(values, 50),
        "p95": _percentile(values, 95),
        "p99": _percentile(values, 99),
    }


async def latency_percentiles(*, limit: int = DEFAULT_TURN_LIMIT) -> dict:
    """Return p50/p95/p99 for each latency segment over the last ``limit`` turns.

    Shape: ``{"sample_size": int, "stt_ms": {p50, p95, p99}, ...}``.
    """

    empty = {seg: _segment_stats([]) for seg in LATENCY_SEGMENTS}
    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    latency_ms AS total_ms,
                    (latency_breakdown->>'stt_ms')::int AS stt_ms,
                    (latency_breakdown->>'llm_ms')::int AS llm_ms,
                    (latency_breakdown->>'tts_first_byte_ms')::int
                        AS tts_first_byte_ms
                FROM call_messages
                WHERE role = 'assistant' AND latency_ms IS NOT NULL
                ORDER BY created_at DESC
                LIMIT $1
                """,
                limit,
            )
    except Exception as exc:
        logger.error("latency_percentiles_failed", error=str(exc))
        return {"sample_size": 0, **empty}

    collected: dict[str, list[int]] = {seg: [] for seg in LATENCY_SEGMENTS}
    for row in rows:
        for seg in LATENCY_SEGMENTS:
            value = row[seg]
            if value is not None:
                collected[seg].append(value)

    return {
        "sample_size": len(rows),
        **{seg: _segment_stats(collected[seg]) for seg in LATENCY_SEGMENTS},
    }
