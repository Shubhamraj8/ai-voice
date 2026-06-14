"""Unit tests for the in-process agent registry (ticket 2.18). No pipeline."""

from unittest.mock import AsyncMock

import pytest
from app.services.voice import agent_registry


@pytest.fixture(autouse=True)
def _clear_registry():
    agent_registry._agents.clear()
    yield
    agent_registry._agents.clear()


def _fake_worker():
    return AsyncMock()


def test_register_increments_active_count():
    agent_registry.register("CA1", _fake_worker())
    assert agent_registry.active_count() == 1

    agent_registry.register("CA2", _fake_worker())
    assert agent_registry.active_count() == 2


def test_unregister_removes_agent():
    agent_registry.register("CA1", _fake_worker())
    agent_registry.unregister("CA1")
    assert agent_registry.active_count() == 0


def test_unregister_unknown_is_noop():
    agent_registry.unregister("nope")
    assert agent_registry.active_count() == 0


def test_list_active_reports_call_sid_and_age():
    agent_registry.register("CA1", _fake_worker())

    active = agent_registry.list_active()

    assert len(active) == 1
    assert active[0]["call_sid"] == "CA1"
    assert active[0]["age_secs"] >= 0


async def test_terminate_cancels_and_removes():
    worker = _fake_worker()
    agent_registry.register("CA1", worker)

    assert await agent_registry.terminate("CA1") is True
    worker.cancel.assert_awaited_once()
    assert agent_registry.active_count() == 0


async def test_terminate_unknown_returns_false():
    assert await agent_registry.terminate("nope") is False


async def test_sweep_force_kills_old_agents():
    worker = _fake_worker()
    agent_registry.register("CA1", worker)

    killed = await agent_registry.sweep(force_kill_age=0, warn_age=0)

    assert killed == 1
    worker.cancel.assert_awaited_once()
    assert agent_registry.active_count() == 0


async def test_sweep_keeps_young_agents():
    worker = _fake_worker()
    agent_registry.register("CA1", worker)

    killed = await agent_registry.sweep(force_kill_age=99999, warn_age=99999)

    assert killed == 0
    worker.cancel.assert_not_awaited()
    assert agent_registry.active_count() == 1


async def test_sweep_warns_long_call_without_killing():
    worker = _fake_worker()
    agent_registry.register("CA1", worker)

    # Past the warn threshold but below force-kill: agent stays, not cancelled.
    killed = await agent_registry.sweep(force_kill_age=99999, warn_age=0)

    assert killed == 0
    worker.cancel.assert_not_awaited()
    assert agent_registry.active_count() == 1
