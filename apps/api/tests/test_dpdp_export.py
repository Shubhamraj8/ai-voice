"""Tests for DPDP data export (ticket 5.12). DB, storage, email mocked."""

import io
import json
import uuid
import zipfile
from datetime import UTC, datetime
from unittest.mock import AsyncMock

from app.services import dpdp_export as de


def test_build_zip_contains_tables_and_documents():
    tables = {
        "tenant": [{"id": uuid.uuid4(), "name": "Acme"}],
        "calls": [{"id": "c1", "started_at": datetime(2026, 6, 1, tzinfo=UTC)}],
        "audit_log": [],
    }
    pdfs = [("doc1_menu.pdf", b"%PDF-1.4 fake")]

    blob = de._build_zip(tables, pdfs)

    archive = zipfile.ZipFile(io.BytesIO(blob))
    names = archive.namelist()
    assert "tenant.json" in names
    assert "calls.json" in names
    assert "audit_log.json" in names
    assert "documents/doc1_menu.pdf" in names
    # JSON is valid and non-serializable types are stringified
    calls = json.loads(archive.read("calls.json"))
    assert calls[0]["id"] == "c1"
    assert calls[0]["started_at"].startswith("2026-06-01")
    assert archive.read("documents/doc1_menu.pdf") == b"%PDF-1.4 fake"


async def test_run_export_uploads_emails_and_scopes(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(de, "get_pool", lambda: pool)
    tid = uuid.uuid4()
    eid = uuid.uuid4()
    doc_id = uuid.uuid4()

    conn.fetchrow.return_value = {"id": tid, "business_name": "Acme"}
    conn.fetch.side_effect = [
        [{"user_id": uuid.uuid4(), "role": "owner"}],  # users
        [{"id": uuid.uuid4(), "name": "Front Desk"}],  # agents
        [{"id": uuid.uuid4()}],  # calls
        [{"id": uuid.uuid4(), "role": "user"}],  # call_messages
        [{"id": doc_id, "storage_path": "t/doc.pdf", "filename": "menu.pdf"}],  # docs
        [{"id": uuid.uuid4(), "event_type": "payment_recorded"}],  # billing_events
        [{"id": uuid.uuid4(), "action": "x"}],  # audit_log
    ]

    monkeypatch.setattr(de, "download_document", AsyncMock(return_value=b"%PDF"))
    upload = AsyncMock(return_value=True)
    monkeypatch.setattr(de, "upload_export", upload)
    monkeypatch.setattr(
        de, "create_export_signed_url", AsyncMock(return_value="https://signed/export")
    )
    send = AsyncMock(return_value=True)
    monkeypatch.setattr(de, "send_email", send)
    audit = AsyncMock()
    monkeypatch.setattr(de, "log_system_action", audit)

    await de.run_dpdp_export(tid, eid, recipient_email="owner@acme.test")

    # uploaded to a per-export path (new ZIP per request, never overwritten)
    upload.assert_awaited_once()
    assert upload.await_args.kwargs["path"] == f"{tid}/{eid}.zip"
    # emailed the 7-day signed link
    assert send.await_args.kwargs["to"] == "owner@acme.test"
    assert "https://signed/export" in send.await_args.kwargs["html"]
    # completed + emailed audit rows
    assert audit.await_count == 2
    # every table query was scoped to this tenant — no cross-tenant leak
    for call in conn.fetch.await_args_list:
        assert call.args[1] == tid


async def test_run_export_without_recipient_skips_email(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(de, "get_pool", lambda: pool)
    conn.fetchrow.return_value = {"id": uuid.uuid4()}
    conn.fetch.side_effect = [[], [], [], [], [], [], []]

    monkeypatch.setattr(de, "upload_export", AsyncMock(return_value=True))
    monkeypatch.setattr(
        de, "create_export_signed_url", AsyncMock(return_value="https://x")
    )
    send = AsyncMock()
    monkeypatch.setattr(de, "send_email", send)
    monkeypatch.setattr(de, "log_system_action", AsyncMock())

    await de.run_dpdp_export(uuid.uuid4(), uuid.uuid4(), recipient_email=None)

    send.assert_not_awaited()
