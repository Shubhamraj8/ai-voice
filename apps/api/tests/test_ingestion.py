"""Tests for knowledge-document ingestion (ticket 4.03).

pdfplumber, tiktoken, OpenAI, storage, and the DB are all mocked — no PDF is
parsed, no vocab is downloaded, no embeddings are computed, and no SQL runs.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

from app.services import ingestion as ing


class _FakeEnc:
    """Word-level stand-in for the tiktoken encoder (deterministic, offline)."""

    def encode(self, text):
        return text.split()

    def decode(self, tokens):
        return " ".join(tokens)


class _FakeTxn:
    async def __aenter__(self):
        return None

    async def __aexit__(self, *args):
        return False


def _doc_row(tenant_id):
    return {"tenant_id": tenant_id, "storage_path": "knowledge/tenant/doc.pdf"}


# --- chunk_text --------------------------------------------------------------


def test_chunk_text_windows_with_overlap(monkeypatch):
    monkeypatch.setattr(ing, "_get_encoding", lambda: _FakeEnc())

    chunks = ing.chunk_text("a b c d e f g", chunk_tokens=4, overlap=1)

    assert [c.content for c in chunks] == ["a b c d", "d e f g"]
    assert chunks[0].token_count == 4
    # overlap: last token of chunk 0 == first token of chunk 1
    assert chunks[0].content.split()[-1] == chunks[1].content.split()[0]


def test_chunk_text_empty_returns_nothing(monkeypatch):
    monkeypatch.setattr(ing, "_get_encoding", lambda: _FakeEnc())
    assert ing.chunk_text("   ") == []


# --- header/footer stripping -------------------------------------------------


def test_remove_headers_footers_drops_repeating_lines():
    pages = [
        ["ACME MENU", "pizza", "page 1"],
        ["ACME MENU", "pasta", "page 1"],
        ["ACME MENU", "salad", "page 1"],
    ]
    cleaned = ing._remove_headers_footers(pages)
    assert cleaned == [["pizza"], ["pasta"], ["salad"]]


def test_remove_headers_footers_noop_for_few_pages():
    pages = [["HEADER", "body"], ["HEADER", "body2"]]
    assert ing._remove_headers_footers(pages) == pages


# --- process_document --------------------------------------------------------


async def test_process_document_success(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    tenant_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    conn.fetchrow.return_value = _doc_row(tenant_id)
    conn.transaction = MagicMock(return_value=_FakeTxn())

    monkeypatch.setattr(ing, "get_pool", lambda: pool)
    monkeypatch.setattr(ing, "download_document", AsyncMock(return_value=b"%PDF"))
    monkeypatch.setattr(ing, "extract_text", lambda data: "menu text")
    monkeypatch.setattr(
        ing,
        "chunk_text",
        lambda text: [ing.Chunk("a", 3), ing.Chunk("b", 2)],
    )
    embed = AsyncMock(return_value=[[0.1, 0.2], [0.3, 0.4]])
    monkeypatch.setattr(ing, "embed_texts", embed)

    await ing.process_document(doc_id)

    embed.assert_awaited_once_with(["a", "b"])
    ing.download_document.assert_awaited_once_with(path="tenant/doc.pdf")

    rows = conn.executemany.await_args.args[1]
    assert len(rows) == 2
    assert rows[0][2] == 0 and rows[0][3] == "a"  # chunk_index, content
    assert rows[0][5] == "[0.1,0.2]"  # vector literal
    sqls = " ".join(c.args[0] for c in conn.execute.await_args_list)
    assert "status='ready'" in sqls


async def test_process_document_download_failure_sets_error(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    conn.fetchrow.return_value = _doc_row(uuid.uuid4())

    monkeypatch.setattr(ing, "get_pool", lambda: pool)
    monkeypatch.setattr(ing, "download_document", AsyncMock(return_value=None))
    embed = AsyncMock()
    monkeypatch.setattr(ing, "embed_texts", embed)

    # Must not raise.
    await ing.process_document(uuid.uuid4())

    embed.assert_not_awaited()
    error_calls = [
        c
        for c in conn.execute.await_args_list
        if "error" in c.args[0] and len(c.args) >= 3
    ]
    assert any(c.args[2] == "error" for c in error_calls)


async def test_process_document_no_text_sets_error(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    conn.fetchrow.return_value = _doc_row(uuid.uuid4())

    monkeypatch.setattr(ing, "get_pool", lambda: pool)
    monkeypatch.setattr(ing, "download_document", AsyncMock(return_value=b"%PDF"))
    monkeypatch.setattr(ing, "extract_text", lambda data: "")
    monkeypatch.setattr(ing, "chunk_text", lambda text: [])
    embed = AsyncMock()
    monkeypatch.setattr(ing, "embed_texts", embed)

    await ing.process_document(uuid.uuid4())

    embed.assert_not_awaited()
    assert any(
        len(c.args) >= 3 and c.args[2] == "error" for c in conn.execute.await_args_list
    )


async def test_process_document_missing_row_is_noop(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    conn.fetchrow.return_value = None
    download = AsyncMock()

    monkeypatch.setattr(ing, "get_pool", lambda: pool)
    monkeypatch.setattr(ing, "download_document", download)

    await ing.process_document(uuid.uuid4())

    download.assert_not_awaited()
    conn.execute.assert_not_awaited()
