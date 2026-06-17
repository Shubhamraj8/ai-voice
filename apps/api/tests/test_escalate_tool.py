"""Tests for the escalateToOwner tool (ticket 4.10). Email/SMS/DB mocked."""

import uuid
from unittest.mock import AsyncMock

from app.tools.base import ToolContext
from app.tools.builtin import escalate as esc
from app.tools.builtin.escalate import EscalateArgs, EscalateToOwner


def _ctx(**kw):
    base = {
        "tenant_id": uuid.uuid4(),
        "agent_id": uuid.uuid4(),
        "call_id": uuid.uuid4(),
    }
    base.update(kw)
    return ToolContext(**base)


def _patch(monkeypatch, *, config, email_ok=True, from_number="+15550000001"):
    monkeypatch.setattr(esc, "get_escalation_config", AsyncMock(return_value=config))
    monkeypatch.setattr(
        esc, "get_caller_number", AsyncMock(return_value="+15559999999")
    )
    monkeypatch.setattr(
        esc, "get_agent_from_number", AsyncMock(return_value=from_number)
    )
    email = AsyncMock(return_value=email_ok)
    sms = AsyncMock(return_value=("SM1", "queued"))
    log = AsyncMock()
    monkeypatch.setattr(esc, "send_email", email)
    monkeypatch.setattr(esc, "send_sms", sms)
    monkeypatch.setattr(esc, "log_escalation", log)
    return email, sms, log


def test_urgency_prefix_mapping():
    assert esc.URGENCY_PREFIX == {
        "high": "[URGENT]",
        "medium": "[HIGH]",
        "low": "[FYI]",
    }


async def test_no_channels_still_succeeds_and_logs(monkeypatch):
    email, sms, log = _patch(
        monkeypatch,
        config={
            "business_name": "Acme",
            "escalation_email": None,
            "escalation_sms": None,
        },
    )

    result = await EscalateToOwner().execute(_ctx(), EscalateArgs(summary="hi"))

    assert result == {"status": "escalated"}
    email.assert_not_awaited()
    sms.assert_not_awaited()
    log.assert_awaited_once()
    assert log.await_args.kwargs["email_sent"] is False
    assert log.await_args.kwargs["sms_sent"] is False


async def test_email_only(monkeypatch):
    email, sms, log = _patch(
        monkeypatch,
        config={
            "business_name": "Acme",
            "escalation_email": "owner@acme.com",
            "escalation_sms": None,
        },
    )

    result = await EscalateToOwner().execute(
        _ctx(), EscalateArgs(summary="angry caller", urgency="high")
    )

    assert result == {"status": "escalated"}
    email.assert_awaited_once()
    assert email.await_args.kwargs["to"] == "owner@acme.com"
    assert email.await_args.kwargs["subject"].startswith("[URGENT]")
    sms.assert_not_awaited()
    assert log.await_args.kwargs["email_sent"] is True


async def test_sms_only(monkeypatch):
    email, sms, log = _patch(
        monkeypatch,
        config={
            "business_name": "Acme",
            "escalation_email": None,
            "escalation_sms": "+15551112222",
        },
    )

    await EscalateToOwner().execute(_ctx(), EscalateArgs(summary="callback please"))

    email.assert_not_awaited()
    sms.assert_awaited_once()
    assert sms.await_args.kwargs["to"] == "+15551112222"
    assert log.await_args.kwargs["sms_sent"] is True


async def test_send_failure_still_succeeds(monkeypatch):
    email, sms, log = _patch(
        monkeypatch,
        config={
            "business_name": "Acme",
            "escalation_email": None,
            "escalation_sms": "+15551112222",
        },
    )
    monkeypatch.setattr(esc, "send_sms", AsyncMock(side_effect=RuntimeError("twilio")))

    result = await EscalateToOwner().execute(_ctx(), EscalateArgs(summary="x"))

    assert result == {"status": "escalated"}
    assert log.await_args.kwargs["sms_sent"] is False
    assert log.await_args.kwargs["error"] == "twilio"


def test_tool_is_registered():
    from app.tools.registry import registry

    assert isinstance(registry.get("escalateToOwner"), EscalateToOwner)
