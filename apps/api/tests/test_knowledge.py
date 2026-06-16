"""Tests for knowledge-document upload (ticket 4.01). External calls mocked."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from app.db.pool import get_pool
from app.main import app
from app.middleware.auth import InternalUserContext, User, require_internal_user
from app.models.knowledge import KnowledgeDocument
from app.services import knowledge
from fastapi import HTTPException
from fastapi.testclient import TestClient

client = TestClient(app)


def _internal_ctx():
    return InternalUserContext(
        user=User(id=uuid.uuid4(), email="internal@example.com"),
        internal_role="admin",
    )


def _doc_row(tenant_id, now):
    return {
        "id": uuid.uuid4(),
        "tenant_id": tenant_id,
        "agent_id": None,
        "filename": "menu.pdf",
        "storage_path": f"knowledge/{tenant_id}/doc.pdf",
        "bytes": 1234,
        "sha256": "abc123",
        "status": "pending",
        "error": None,
        "uploaded_at": now,
        "processed_at": None,
    }


# --- validation --------------------------------------------------------------


def test_compute_sha256_is_deterministic():
    assert knowledge.compute_sha256(b"hello") == knowledge.compute_sha256(b"hello")
    assert knowledge.compute_sha256(b"a") != knowledge.compute_sha256(b"b")


def test_validate_pdf_rejects_non_pdf():
    with pytest.raises(HTTPException) as exc:
        knowledge.validate_pdf(data=b"x", content_type="text/plain")
    assert exc.value.detail["code"] == "unsupported_media_type"


def test_validate_pdf_rejects_too_large():
    big = b"x" * (knowledge.MAX_BYTES + 1)
    with pytest.raises(HTTPException) as exc:
        knowledge.validate_pdf(data=big, content_type="application/pdf")
    assert exc.value.detail["code"] == "file_too_large"


def test_validate_pdf_rejects_too_many_pages(monkeypatch):
    monkeypatch.setattr(knowledge, "_pdf_page_count", lambda data: 600)
    with pytest.raises(HTTPException) as exc:
        knowledge.validate_pdf(data=b"%PDF-1.4", content_type="application/pdf")
    assert exc.value.detail["code"] == "too_many_pages"


def test_validate_pdf_accepts_valid(monkeypatch):
    monkeypatch.setattr(knowledge, "_pdf_page_count", lambda data: 10)
    assert (
        knowledge.validate_pdf(data=b"%PDF-1.4", content_type="application/pdf") == 10
    )


# --- store_document ----------------------------------------------------------


async def test_store_document_success(mock_db_pool, monkeypatch):
    _pool, conn = mock_db_pool
    tenant_id = uuid.uuid4()
    now = datetime.now(UTC)
    conn.fetchrow.side_effect = [None, _doc_row(tenant_id, now)]
    monkeypatch.setattr(knowledge, "upload_document", AsyncMock(return_value=True))

    doc = await knowledge.store_document(
        conn, tenant_id=tenant_id, filename="menu.pdf", data=b"%PDF", sha256="abc123"
    )

    assert doc.filename == "menu.pdf"
    assert doc.status == "pending"
    knowledge.upload_document.assert_awaited_once()


async def test_store_document_rejects_duplicate(mock_db_pool, monkeypatch):
    _pool, conn = mock_db_pool
    conn.fetchrow.return_value = {"id": uuid.uuid4()}
    upload = AsyncMock(return_value=True)
    monkeypatch.setattr(knowledge, "upload_document", upload)

    with pytest.raises(HTTPException) as exc:
        await knowledge.store_document(
            conn, tenant_id=uuid.uuid4(), filename="m.pdf", data=b"x", sha256="dup"
        )
    assert exc.value.detail["code"] == "duplicate_document"
    upload.assert_not_awaited()


async def test_store_document_upload_failure(mock_db_pool, monkeypatch):
    _pool, conn = mock_db_pool
    conn.fetchrow.return_value = None
    monkeypatch.setattr(knowledge, "upload_document", AsyncMock(return_value=False))

    with pytest.raises(HTTPException) as exc:
        await knowledge.store_document(
            conn, tenant_id=uuid.uuid4(), filename="m.pdf", data=b"x", sha256="abc"
        )
    assert exc.value.detail["code"] == "upload_failed"


# --- upload endpoint ---------------------------------------------------------


def test_upload_endpoint_creates_document(mock_db_pool, monkeypatch):
    pool, _conn = mock_db_pool
    tenant_id = uuid.uuid4()
    now = datetime.now(UTC)
    doc = KnowledgeDocument.model_validate(_doc_row(tenant_id, now))

    monkeypatch.setattr(
        "app.routes.internal_knowledge.validate_pdf", lambda **kwargs: 10
    )

    async def fake_store(conn, **kwargs):
        return doc

    monkeypatch.setattr("app.routes.internal_knowledge.store_document", fake_store)
    audit = AsyncMock()
    monkeypatch.setattr("app.routes.internal_knowledge.log_internal_action", audit)
    ingest = AsyncMock()
    monkeypatch.setattr("app.routes.internal_knowledge.process_document", ingest)

    app.dependency_overrides[require_internal_user] = _internal_ctx
    app.dependency_overrides[get_pool] = lambda: pool
    try:
        response = client.post(
            f"/internal/tenants/{tenant_id}/knowledge",
            files={"file": ("menu.pdf", b"%PDF-1.4 fake", "application/pdf")},
        )
        assert response.status_code == 201
        assert response.json()["filename"] == "menu.pdf"
        audit.assert_awaited_once()
        ingest.assert_awaited_once_with(doc.id)
    finally:
        app.dependency_overrides.clear()
