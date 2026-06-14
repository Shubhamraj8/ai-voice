"""Background sweeper for long-running / orphaned agents (ticket 2.18).

Periodically warns on long calls and force-kills agents that outlive the safety
cap (e.g. a websocket that died without cleaning up). Mirrors the stale-call
reaper pattern.
"""

from __future__ import annotations

import asyncio

import structlog

from app.services.voice import agent_registry

logger = structlog.get_logger(__name__)

SWEEP_INTERVAL_SECONDS = 60


async def run_agent_sweeper(*, interval_seconds: int = SWEEP_INTERVAL_SECONDS) -> None:
    """Loop forever sweeping the agent registry; cancel the task to stop it."""

    logger.info("agent_sweeper_started", interval_seconds=interval_seconds)
    try:
        while True:
            await asyncio.sleep(interval_seconds)
            try:
                await agent_registry.sweep()
            except Exception as exc:  # never let one bad pass kill the loop
                logger.error("agent_sweeper_pass_failed", error=str(exc))
    except asyncio.CancelledError:
        logger.info("agent_sweeper_stopped")
        raise
