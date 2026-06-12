"""Background reaper that closes calls dropped before a status callback (2.13).

A call whose Twilio status callback never arrives (caller hangs up hard, network
drop) would otherwise keep ``ended_at = NULL`` forever. This periodic task closes
any call open longer than ``STALE_CALL_MAX_AGE_SECONDS``.
"""

from __future__ import annotations

import asyncio

import structlog

from app.services.calls import close_stale_calls

logger = structlog.get_logger(__name__)

# How often the reaper runs.
REAPER_INTERVAL_SECONDS = 300
# A call still open after this long is treated as dropped.
STALE_CALL_MAX_AGE_SECONDS = 3600


async def run_stale_call_reaper(
    *,
    interval_seconds: int = REAPER_INTERVAL_SECONDS,
    max_age_seconds: int = STALE_CALL_MAX_AGE_SECONDS,
) -> None:
    """Loop forever closing stale calls; cancel the task to stop it."""

    logger.info(
        "stale_call_reaper_started",
        interval_seconds=interval_seconds,
        max_age_seconds=max_age_seconds,
    )
    try:
        while True:
            await asyncio.sleep(interval_seconds)
            try:
                await close_stale_calls(max_age_seconds=max_age_seconds)
            except Exception as exc:  # never let one bad pass kill the loop
                logger.error("stale_call_reaper_pass_failed", error=str(exc))
    except asyncio.CancelledError:
        logger.info("stale_call_reaper_stopped")
        raise
