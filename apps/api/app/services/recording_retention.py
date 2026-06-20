"""30-day call-recording retention (ticket 5.15).

A daily job (03:00 IST) purges call audio older than the retention window from
Storage and nulls ``recording_url`` (recording ``recording_deleted_at``). Only
the audio is removed — transcripts (``call_messages``) are kept, and the portal
shows "Recording expired" once the file is gone. Idempotent: a missing Storage
file is a no-op, and rows already purged are excluded by the WHERE clause.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import structlog

from app.db.pool import get_pool
from app.services.audit import log_system_action
from app.services.storage import delete_recording

logger = structlog.get_logger(__name__)

RETENTION_DAYS = 30  # global for v1; per-plan override is a later enhancement
RUN_HOUR_IST = 3
IST = timezone(timedelta(hours=5, minutes=30))


def seconds_until_next_run(now: datetime | None = None) -> float:
    """Seconds until the next 03:00 IST."""
    now = now or datetime.now(IST)
    target = now.replace(hour=RUN_HOUR_IST, minute=0, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


async def purge_old_recordings(*, retention_days: int = RETENTION_DAYS) -> int:
    """Delete recordings whose call ended over ``retention_days`` ago. Returns the
    number of recordings purged."""

    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, recording_url FROM calls "
                "WHERE recording_url IS NOT NULL "
                "AND ended_at < now() - make_interval(days => $1)",
                retention_days,
            )
            for row in rows:
                # Best-effort + idempotent: a 404 on an already-gone file is fine.
                await delete_recording(path=row["recording_url"])
                await conn.execute(
                    "UPDATE calls SET recording_url = NULL, "
                    "recording_deleted_at = now() WHERE id = $1",
                    row["id"],
                )
    except Exception as exc:
        logger.error("recording_retention_failed", error=str(exc))
        return 0

    if rows:
        await log_system_action(
            action="recording.retention.purged",
            payload={"count": len(rows), "retention_days": retention_days},
        )
        logger.info("recordings_purged", count=len(rows))
    return len(rows)


async def run_recording_retention() -> None:
    """Loop forever, purging once per day at 03:00 IST; cancel to stop."""

    logger.info("recording_retention_started", run_hour_ist=RUN_HOUR_IST)
    try:
        while True:
            await asyncio.sleep(seconds_until_next_run())
            await purge_old_recordings()
    except asyncio.CancelledError:
        logger.info("recording_retention_stopped")
        raise
