"""Tests for the sendSms tool + sms_log helpers (ticket 4.09). Twilio + DB mocked."""

import uuid
from unittest.mock import AsyncMock

from app.services import sms as sms_service
from app.tools.base import ToolContext
from app.tools.builtin import sms as sms_tool
from app.tools.builtin.sms import SendSms, SmsArgs


def _ctx(**kw):
    base = {
        "tenant_id": uuid.uuid4(),
        "agent_id": uuid.uuid4(),
        "call_id": uuid.uuid4(),
    }
    base.update(kw)
    return ToolContext(**base)


# --- truncate ----------------------------------------------------------------


def test_truncate_short_unchanged():
    assert sms_service.truncate_sms("hi there") == "hi there"


def test_truncate_long_marks_ellipsis():
    out = sms_service.truncate_sms("x" * 400)
    assert len(out) == sms_service.MAX_SMS_CHARS
    assert out.endswith("…")


# --- SendSms.execute ---------------------------------------------------------


async def test_missing_from_number_errors(monkeypatch):
    monkeypatch.setattr(sms_tool, "get_agent_from_number", AsyncMock(return_value=None))
    send = AsyncMock()
    monkeypatch.setattr(sms_tool, "send_sms", send)

    result = await SendSms().execute(_ctx(), SmsArgs(body="hi"))

    assert "error" in result
    send.assert_not_awaited()


async def test_defaults_recipient_to_caller(monkeypatch):
    monkeypatch.setattr(
        sms_tool, "get_agent_from_number", AsyncMock(return_value="+15550000001")
    )
    monkeypatch.setattr(
        sms_tool, "get_caller_number", AsyncMock(return_value="+15559999999")
    )
    send = AsyncMock(return_value=("SM123", "queued"))
    monkeypatch.setattr(sms_tool, "send_sms", send)
    monkeypatch.setattr(sms_tool, "log_sms", AsyncMock())

    result = await SendSms().execute(_ctx(), SmsArgs(body="hello"))

    assert result == {"status": "queued", "sid": "SM123", "to": "+15559999999"}
    assert send.await_args.kwargs["to"] == "+15559999999"
    assert send.await_args.kwargs["from_"] == "+15550000001"


async def test_no_recipient_errors(monkeypatch):
    monkeypatch.setattr(
        sms_tool, "get_agent_from_number", AsyncMock(return_value="+15550000001")
    )
    monkeypatch.setattr(sms_tool, "get_caller_number", AsyncMock(return_value=None))
    send = AsyncMock()
    monkeypatch.setattr(sms_tool, "send_sms", send)

    result = await SendSms().execute(_ctx(), SmsArgs(body="hi"))

    assert "error" in result
    send.assert_not_awaited()


async def test_success_logs_sms(monkeypatch):
    monkeypatch.setattr(
        sms_tool, "get_agent_from_number", AsyncMock(return_value="+15550000001")
    )
    monkeypatch.setattr(sms_tool, "send_sms", AsyncMock(return_value=("SM9", "sent")))
    log = AsyncMock()
    monkeypatch.setattr(sms_tool, "log_sms", log)

    result = await SendSms().execute(_ctx(), SmsArgs(body="hi", to="+15551112222"))

    assert result["sid"] == "SM9"
    log.assert_awaited_once()
    assert log.await_args.kwargs["twilio_sid"] == "SM9"
    assert log.await_args.kwargs["status"] == "sent"


async def test_twilio_error_logs_failure(monkeypatch):
    monkeypatch.setattr(
        sms_tool, "get_agent_from_number", AsyncMock(return_value="+15550000001")
    )
    monkeypatch.setattr(
        sms_tool, "send_sms", AsyncMock(side_effect=RuntimeError("twilio down"))
    )
    log = AsyncMock()
    monkeypatch.setattr(sms_tool, "log_sms", log)

    result = await SendSms().execute(_ctx(), SmsArgs(body="hi", to="+15551112222"))

    assert "error" in result
    assert log.await_args.kwargs["status"] == "failed"
    assert log.await_args.kwargs["twilio_sid"] is None


def test_tool_is_registered():
    from app.tools.registry import registry

    assert isinstance(registry.get("sendSms"), SendSms)


# --- update_sms_status -------------------------------------------------------


async def test_update_sms_status(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(sms_service, "get_pool", lambda: pool)

    await sms_service.update_sms_status("SM123", "delivered")

    conn.execute.assert_awaited_once()
    args = conn.execute.await_args.args
    assert args[1] == "SM123"
    assert args[2] == "delivered"
