"""Knowledge-document upload + validation (ticket 4.01).

Validates a PDF (type, size, page count), dedupes by content hash, uploads it to
the private knowledge bucket, and records a ``knowledge_documents`` row in
``pending`` status. Ingestion (extraction + embeddings) is ticket 4.03.
"""

from __future__ import annotations

import hashlib
import io
from uuid import UUID, uuid4

import structlog

from app.config import get_settings
from app.errors import api_error
from app.models.knowledge import KnowledgeDocument
from app.services.storage import upload_document

logger = structlog.get_logger(__name__)

MAX_BYTES = 20 * 1024 * 1024  # 20 MB
MAX_PAGES = 500
_PDF_CONTENT_TYPES = {"application/pdf", "application/x-pdf"}


def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _pdf_page_count(data: bytes) -> int:
    # Lazy import — pdfplumber is heavy and only needed for validation/ingestion.
    import pdfplumber

    with pdfplumber.open(io.BytesIO(data)) as pdf:
        return len(pdf.pages)


def validate_pdf(*, data: bytes, content_type: str | None) -> int:
    """Validate a PDF upload; return its page count or raise an api_error."""

    if content_type not in _PDF_CONTENT_TYPES:
        raise api_error(415, "unsupported_media_type", "Only PDF uploads are allowed")
    if not data:
        raise api_error(400, "empty_file", "The uploaded file is empty")
    if len(data) > MAX_BYTES:
        raise api_error(400, "file_too_large", "PDF exceeds the 20MB limit")

    try:
        pages = _pdf_page_count(data)
    except Exception as exc:
        raise api_error(400, "invalid_pdf", f"Could not read the PDF: {exc}")

    if pages > MAX_PAGES:
        raise api_error(
            400, "too_many_pages", f"PDF has {pages} pages (max {MAX_PAGES})"
        )
    return pages


async def store_document(
    conn,
    *,
    tenant_id: UUID,
    filename: str,
    data: bytes,
    sha256: str,
    agent_id: UUID | None = None,
) -> KnowledgeDocument:
    """Upload the file and insert its ``knowledge_documents`` row (pending).

    Raises 409 if the same content was already uploaded for this tenant, or 502
    if the storage upload fails.
    """

    existing = await conn.fetchrow(
        "SELECT id FROM knowledge_documents WHERE tenant_id = $1 AND sha256 = $2",
        tenant_id,
        sha256,
    )
    if existing is not None:
        raise api_error(409, "duplicate_document", "This document was already uploaded")

    doc_id = uuid4()
    object_path = f"{tenant_id}/{doc_id}.pdf"
    storage_path = f"{get_settings().knowledge_bucket}/{object_path}"

    if not await upload_document(path=object_path, data=data):
        raise api_error(502, "upload_failed", "Could not store the document")

    row = await conn.fetchrow(
        """
        INSERT INTO knowledge_documents (
            id, tenant_id, agent_id, filename, storage_path, bytes, sha256
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING *
        """,
        doc_id,
        tenant_id,
        agent_id,
        filename,
        storage_path,
        len(data),
        sha256,
    )
    logger.info(
        "knowledge_document_stored",
        tenant_id=str(tenant_id),
        document_id=str(doc_id),
        bytes=len(data),
    )
    return KnowledgeDocument.model_validate(dict(row))
