"""Tests for DPDP data deletion (ticket 5.13). DB, storage, auth, email mocked."""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.services import dpdp_delete as dd
from fastapi import HTTPException


class _FakeTxn:
    async def __aenter__(self):
        return None

    async def __aexit__(self, *args):
        return False


async def test_request_deletion_creates_token_and_emails(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(dd, "get_pool", lambda: pool)
    conn.fetchrow.return_value = {"deletion_blocked": False, "deleted_at": None}
    send = AsyncMock(return_value=True)
    monkeypatch.setattr(dd, "send_email", send)

    result = await dd.request_deletion(
        uuid.uuid4(), requested_by=uuid.uuid4(), recipient_email="owner@acme.test"
    )

    assert result["status"] == "confirmation_sent"
    conn.execute.assert_awaited_once()  # inserted the request row
    assert "INSERT INTO dpdp_deletion_requests" in conn.execute.await_args.args[0]
    assert "/confirm-delete?token=" in send.await_args.kwargs["html"]


async def test_request_deletion_blocked(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(dd, "get_pool", lambda: pool)
    conn.fetchrow.return_value = {"deletion_blocked": True, "deleted_at": None}
    monkeypatch.setattr(dd, "send_email", AsyncMock())

    with pytest.raises(HTTPException) as exc:
        await dd.request_deletion(
            uuid.uuid4(), requested_by=uuid.uuid4(), recipient_email="x@y.test"
        )

    assert exc.value.status_code == 403
    conn.execute.assert_not_awaited()


async def test_request_deletion_already_deleted(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(dd, "get_pool", lambda: pool)
    conn.fetchrow.return_value = {
        "deletion_blocked": False,
        "deleted_at": datetime.now(UTC),
    }

    with pytest.raises(HTTPException) as exc:
        await dd.request_deletion(
            uuid.uuid4(), requested_by=uuid.uuid4(), recipient_email="x@y.test"
        )

    assert exc.value.status_code == 409


async def test_confirm_deletion_schedules(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(dd, "get_pool", lambda: pool)
    tid, rid = uuid.uuid4(), uuid.uuid4()
    conn.fetchrow.return_value = {
        "id": rid,
        "tenant_id": tid,
        "recipient_email": "owner@acme.test",
        "status": "pending",
        "expires_at": datetime.now(UTC) + timedelta(hours=1),
    }
    monkeypatch.setattr(dd, "log_system_action", AsyncMock())
    scheduled = MagicMock()
    monkeypatch.setattr(dd, "schedule_deletion", scheduled)

    result = await dd.confirm_deletion("rawtoken")

    assert result["status"] == "confirmed"
    assert "status = 'confirmed'" in conn.execute.await_args.args[0]
    scheduled.assert_called_once_with(tid, rid, recipient_email="owner@acme.test")


async def test_confirm_deletion_invalid_token(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(dd, "get_pool", lambda: pool)
    conn.fetchrow.return_value = None

    with pytest.raises(HTTPException) as exc:
        await dd.confirm_deletion("nope")
    assert exc.value.status_code == 404


async def test_confirm_deletion_expired(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(dd, "get_pool", lambda: pool)
    conn.fetchrow.return_value = {
        "id": uuid.uuid4(),
        "tenant_id": uuid.uuid4(),
        "recipient_email": "x@y.test",
        "status": "pending",
        "expires_at": datetime.now(UTC) - timedelta(hours=1),
    }

    with pytest.raises(HTTPException) as exc:
        await dd.confirm_deletion("expired")
    assert exc.value.status_code == 410


async def test_run_deletion_wipes_storage_users_and_db(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(dd, "get_pool", lambda: pool)
    conn.transaction = MagicMock(return_value=_FakeTxn())
    conn.fetch.side_effect = [
        [{"recording_url": "t/c1.mp3"}],  # recordings
        [{"storage_path": "t/d1.pdf"}],  # knowledge docs
        [{"twilio_sid": "PN123"}],  # agent numbers
        [{"user_id": uuid.uuid4()}],  # tenant users
    ]
    rec = AsyncMock(return_value=True)
    doc = AsyncMock(return_value=True)
    web = AsyncMock()
    usr = AsyncMock(return_value=True)
    send = AsyncMock(return_value=True)
    audit = AsyncMock()
    monkeypatch.setattr(dd, "delete_recording", rec)
    monkeypatch.setattr(dd, "delete_document", doc)
    monkeypatch.setattr(dd, "clear_voice_webhook", web)
    monkeypatch.setattr(dd, "delete_user", usr)
    monkeypatch.setattr(dd, "send_email", send)
    monkeypatch.setattr(dd, "log_system_action", audit)

    await dd.run_deletion(uuid.uuid4(), uuid.uuid4(), recipient_email="owner@acme.test")

    rec.assert_awaited_once_with(path="t/c1.mp3")
    doc.assert_awaited_once_with(path="t/d1.pdf")
    web.assert_awaited_once_with("PN123")
    usr.assert_awaited_once()
    # the 6 DB mutations ran
    sqls = " ".join(c.args[0] for c in conn.execute.await_args_list)
    assert "DELETE FROM call_messages" in sqls
    assert "DELETE FROM knowledge_embeddings" in sqls
    assert "UPDATE calls SET from_number = NULL" in sqls
    assert "status = 'churned'" in sqls and "paid_until = NULL" in sqls
    assert "DELETE FROM tenant_users" in sqls
    assert "status = 'completed'" in sqls
    send.assert_awaited_once()  # completion email
    audit.assert_awaited_once()  # completion audit
