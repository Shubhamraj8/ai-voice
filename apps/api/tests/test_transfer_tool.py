"""Tests for the transferToHuman tool (ticket 4.08). Twilio + DB mocked."""

import uuid
from unittest.mock import AsyncMock

from app.tools.base import ToolContext
from app.tools.builtin import transfer
from app.tools.builtin.transfer import TransferArgs, TransferToHuman


def _ctx(**kw):
    base = {
        "tenant_id": uuid.uuid4(),
        "agent_id": uuid.uuid4(),
        "call_id": uuid.uuid4(),
        "twilio_call_sid": "CA123",
    }
    base.update(kw)
    return ToolContext(**base)


async def test_no_active_call_returns_error(monkeypatch):
    call = AsyncMock()
    monkeypatch.setattr(transfer, "transfer_call", call)

    result = await TransferToHuman().execute(_ctx(twilio_call_sid=None), TransferArgs())

    assert "error" in result
    call.assert_not_awaited()


async def test_missing_number_returns_error(monkeypatch):
    monkeypatch.setattr(
        transfer, "_agent_transfer_number", AsyncMock(return_value=None)
    )
    call = AsyncMock()
    monkeypatch.setattr(transfer, "transfer_call", call)
    outcome = AsyncMock()
    monkeypatch.setattr(transfer, "set_call_outcome", outcome)

    result = await TransferToHuman().execute(_ctx(), TransferArgs())

    assert result["error"] == "no transfer number is configured for this agent"
    call.assert_not_awaited()
    outcome.assert_not_awaited()


async def test_transfer_failure_returns_error(monkeypatch):
    monkeypatch.setattr(
        transfer, "_agent_transfer_number", AsyncMock(return_value="+15551234567")
    )
    monkeypatch.setattr(transfer, "transfer_call", AsyncMock(return_value=False))
    outcome = AsyncMock()
    monkeypatch.setattr(transfer, "set_call_outcome", outcome)

    result = await TransferToHuman().execute(_ctx(), TransferArgs())

    assert "error" in result
    outcome.assert_not_awaited()  # outcome not marked on failure


async def test_successful_transfer(monkeypatch):
    monkeypatch.setattr(
        transfer, "_agent_transfer_number", AsyncMock(return_value="+15551234567")
    )
    call = AsyncMock(return_value=True)
    monkeypatch.setattr(transfer, "transfer_call", call)
    outcome = AsyncMock()
    monkeypatch.setattr(transfer, "set_call_outcome", outcome)

    ctx = _ctx()
    result = await TransferToHuman().execute(ctx, TransferArgs(reason="caller asked"))

    assert result == {"status": "transferring", "to": "+15551234567"}
    call.assert_awaited_once()
    assert call.await_args.args[0] == "CA123"
    assert call.await_args.args[1] == "+15551234567"
    outcome.assert_awaited_once_with(ctx.call_id, "transferred")


def test_tool_is_registered():
    from app.tools.registry import registry

    assert isinstance(registry.get("transferToHuman"), TransferToHuman)
