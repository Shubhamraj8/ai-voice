"""Tests for sample-chunk listing (ticket 4.15). DB mocked, no pipecat import."""

import uuid

import pytest
from app.services import knowledge
from fastapi import HTTPException


async def test_list_document_chunks_returns_rows(mock_db_pool):
    _pool, conn = mock_db_pool
    tenant_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    conn.fetchrow.return_value = {"id": doc_id}
    conn.fetch.return_value = [
        {"chunk_index": 0, "content": "first", "token_count": 10},
        {"chunk_index": 1, "content": "second", "token_count": 12},
    ]

    chunks = await knowledge.list_document_chunks(
        conn, tenant_id=tenant_id, document_id=doc_id, limit=3
    )

    assert [c["chunk_index"] for c in chunks] == [0, 1]
    assert chunks[0]["content"] == "first"


async def test_list_document_chunks_404_for_other_tenant(mock_db_pool):
    _pool, conn = mock_db_pool
    conn.fetchrow.return_value = None  # doc not found for this tenant

    with pytest.raises(HTTPException) as exc:
        await knowledge.list_document_chunks(
            conn, tenant_id=uuid.uuid4(), document_id=uuid.uuid4()
        )
    assert exc.value.status_code == 404
