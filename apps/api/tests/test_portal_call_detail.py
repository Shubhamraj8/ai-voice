"""Tests for the portal call detail (ticket 5.10). DB + storage mocked."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

from app.services import portal_call_detail as pcd


def _call_row(**over):
    base = {
        "id": uuid.uuid4(),
        "from_number": "+919876543210",
        "started_at": datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
        "ended_at": datetime(2026, 6, 18, 10, 3, tzinfo=UTC),
        "duration_secs": 180,
        "outcome": "booked",
        "intent": "appointment",
        "summary": "Booked a slot",
        "recording_url": "tenant/call.mp3",
        "recording_deleted_at": None,
        "agent_name": "Front Desk",
    }
    base.update(over)
    return base


async def test_call_detail_splits_transcript_and_tools(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(pcd, "get_pool", lambda: pool)
    signer = AsyncMock(return_value="https://signed.example/audio")
    monkeypatch.setattr(pcd, "create_signed_url", signer)

    tid = uuid.uuid4()
    call_id = uuid.uuid4()
    conn.fetchrow.side_effect = [
        _call_row(id=call_id),  # call
        {  # escalation
            "summary": "Customer is upset",
            "urgency": "high",
            "created_at": datetime(2026, 6, 18, 10, 2, tzinfo=UTC),
        },
    ]
    conn.fetch.return_value = [
        {
            "role": "user",
            "content": "Hi",
            "tool_name": None,
            "tool_args": None,
            "tool_result": None,
            "latency_ms": None,
            "created_at": datetime(2026, 6, 18, 10, 0, 5, tzinfo=UTC),
        },
        {
            "role": "assistant",
            "content": "Hello!",
            "tool_name": None,
            "tool_args": None,
            "tool_result": None,
            "latency_ms": 120,
            "created_at": datetime(2026, 6, 18, 10, 0, 7, tzinfo=UTC),
        },
        {
            "role": "tool",
            "content": '{"status": "sent"}',
            "tool_name": "sendSms",
            "tool_args": '{"to": "+919876543210", "body": "Your booking is confirmed"}',
            "tool_result": '{"status": "queued", "to": "+919876543210"}',
            "latency_ms": None,
            "created_at": datetime(2026, 6, 18, 10, 1, tzinfo=UTC),
        },
    ]

    detail = await pcd.get_call_detail(tid, call_id)

    assert detail is not None
    assert detail.agent_name == "Front Desk"
    # transcript = conversational turns only
    assert [m.role for m in detail.transcript] == ["user", "assistant"]
    # tool dispatch separated out, phone scrubbed in args AND result
    assert len(detail.tools) == 1
    tool = detail.tools[0]
    assert tool.tool_name == "sendSms"
    assert tool.tool_args["to"] == "+91 XXXXX X3210"
    assert tool.tool_args["body"] == "Your booking is confirmed"  # untouched
    assert tool.tool_result["to"] == "+91 XXXXX X3210"
    assert "9876543210" not in str(tool.tool_args) + str(tool.tool_result)
    # escalation + fresh 1h signed URL
    assert detail.escalation.urgency == "high"
    assert detail.recording_signed_url == "https://signed.example/audio"
    signer.assert_awaited_once_with(path="tenant/call.mp3", expires_in=3600)


async def test_call_detail_not_found_returns_none(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(pcd, "get_pool", lambda: pool)
    conn.fetchrow.return_value = None  # call missing / not this tenant

    detail = await pcd.get_call_detail(uuid.uuid4(), uuid.uuid4())

    assert detail is None
    conn.fetch.assert_not_awaited()


async def test_call_detail_no_recording_skips_signing(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(pcd, "get_pool", lambda: pool)
    signer = AsyncMock()
    monkeypatch.setattr(pcd, "create_signed_url", signer)
    conn.fetchrow.side_effect = [_call_row(recording_url=None), None]
    conn.fetch.return_value = []

    detail = await pcd.get_call_detail(uuid.uuid4(), uuid.uuid4())

    assert detail.recording_signed_url is None
    assert detail.recording_expired is False
    signer.assert_not_awaited()


async def test_call_detail_recording_expired(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(pcd, "get_pool", lambda: pool)
    signer = AsyncMock()
    monkeypatch.setattr(pcd, "create_signed_url", signer)
    # audio purged by the retention job: url nulled, recording_deleted_at set
    conn.fetchrow.side_effect = [
        _call_row(recording_url=None, recording_deleted_at=datetime.now(UTC)),
        None,
    ]
    conn.fetch.return_value = []

    detail = await pcd.get_call_detail(uuid.uuid4(), uuid.uuid4())

    assert detail.recording_signed_url is None
    assert detail.recording_expired is True
    signer.assert_not_awaited()
