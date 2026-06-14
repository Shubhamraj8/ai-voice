"""In-memory registry of active voice-pipeline agents (ticket 2.18).

Each Twilio call runs one in-process Pipecat pipeline worker (not a separate OS
process). This registry tracks them by ``call_sid`` so they can be counted,
terminated on call end, and force-killed if they outlive a sane call.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from pipecat.pipeline.worker import PipelineWorker

logger = structlog.get_logger(__name__)

# The ideal call is ~3 min; these are safety caps well above it (see memory
# "ideal-call-duration"). A long call is warned at 6 min, force-killed at 10.
LONG_CALL_WARN_AGE_SECONDS = 360
FORCE_KILL_AGE_SECONDS = 600


@dataclass
class _AgentHandle:
    call_sid: str
    worker: PipelineWorker
    started_at: float
    warned: bool = False


_agents: dict[str, _AgentHandle] = {}


def register(call_sid: str, worker: PipelineWorker) -> None:
    _agents[call_sid] = _AgentHandle(
        call_sid=call_sid, worker=worker, started_at=time.monotonic()
    )
    logger.info("agent_registered", call_sid=call_sid, active=len(_agents))


def unregister(call_sid: str) -> None:
    if _agents.pop(call_sid, None) is not None:
        logger.info("agent_unregistered", call_sid=call_sid, active=len(_agents))


def active_count() -> int:
    return len(_agents)


def list_active() -> list[dict[str, object]]:
    now = time.monotonic()
    return [
        {"call_sid": handle.call_sid, "age_secs": round(now - handle.started_at)}
        for handle in _agents.values()
    ]


async def _cancel(handle: _AgentHandle) -> None:
    try:
        await handle.worker.cancel()
    except Exception as exc:
        logger.error("agent_cancel_failed", call_sid=handle.call_sid, error=str(exc))


async def terminate(call_sid: str) -> bool:
    """Cancel and deregister an agent. Returns True if one was registered."""

    handle = _agents.pop(call_sid, None)
    if handle is None:
        return False
    await _cancel(handle)
    logger.info("agent_terminated", call_sid=call_sid, active=len(_agents))
    return True


async def sweep(
    *,
    force_kill_age: int = FORCE_KILL_AGE_SECONDS,
    warn_age: int = LONG_CALL_WARN_AGE_SECONDS,
) -> int:
    """Warn on long-running calls and force-kill agents past ``force_kill_age``.

    A registered agent that outlives the cap is treated as stuck/orphaned — its
    call ended without cleanup — and is cancelled. Returns the count killed.
    """

    now = time.monotonic()
    killed = 0
    for handle in list(_agents.values()):
        age = now - handle.started_at
        if age >= force_kill_age:
            logger.warning(
                "agent_force_killed", call_sid=handle.call_sid, age_secs=round(age)
            )
            _agents.pop(handle.call_sid, None)
            await _cancel(handle)
            killed += 1
        elif age >= warn_age and not handle.warned:
            handle.warned = True
            logger.warning(
                "agent_long_call", call_sid=handle.call_sid, age_secs=round(age)
            )
    return killed
