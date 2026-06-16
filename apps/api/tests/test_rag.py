"""Tests for RAG retrieval + injection logic (ticket 4.06).

Pure logic only — no pipecat/scipy import. retrieve_for_query is mocked.
"""

import uuid
from unittest.mock import AsyncMock

from app.services.knowledge_retrieval import RetrievedChunk
from app.services.voice import rag


def _chunk(idx, content, similarity):
    return RetrievedChunk(
        document_id=uuid.uuid4(),
        chunk_index=idx,
        content=content,
        similarity=similarity,
    )


# --- formatting --------------------------------------------------------------


def test_format_knowledge_block_has_prefix_chunks_and_fallback():
    block = rag.format_knowledge_block([_chunk(0, "We open at 9am.", 0.9)])
    assert block.startswith(rag.KNOWLEDGE_PREFIX)
    assert "We open at 9am." in block
    assert rag.FALLBACK_INSTRUCTION in block


# --- latest_user_query -------------------------------------------------------


def test_latest_user_query_returns_most_recent_user():
    messages = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "reply"},
        {"role": "user", "content": "second"},
    ]
    assert rag.latest_user_query(messages) == "second"


def test_latest_user_query_none_when_no_user():
    messages = [
        {"role": "system", "content": "sys"},
        {"role": "assistant", "content": "hi"},
    ]
    assert rag.latest_user_query(messages) is None


def test_latest_user_query_skips_empty():
    messages = [{"role": "user", "content": "   "}]
    assert rag.latest_user_query(messages) is None


# --- inject_knowledge --------------------------------------------------------


def test_inject_knowledge_inserts_before_last_user():
    messages = [
        {"role": "system", "content": "sys"},
        {"role": "assistant", "content": "hi"},
        {"role": "user", "content": "q1"},
    ]
    result = rag.inject_knowledge(messages, "KB BLOCK")
    assert result[-1] == {"role": "user", "content": "q1"}
    assert result[-2] == {"role": "system", "content": "KB BLOCK"}


def test_inject_knowledge_replaces_previous_block():
    block1 = f"{rag.KNOWLEDGE_PREFIX} old"
    messages = [
        {"role": "system", "content": "sys"},
        {"role": "system", "content": block1},
        {"role": "user", "content": "q1"},
        {"role": "assistant", "content": "a1"},
        {"role": "user", "content": "q2"},
    ]
    block2 = f"{rag.KNOWLEDGE_PREFIX} new"
    result = rag.inject_knowledge(messages, block2)

    kb_blocks = [m for m in result if m["content"].startswith(rag.KNOWLEDGE_PREFIX)]
    assert kb_blocks == [{"role": "system", "content": block2}]
    # placed right before the latest user turn
    assert (
        result[result.index({"role": "user", "content": "q2"}) - 1]["content"] == block2
    )


# --- retrieve_and_format -----------------------------------------------------


async def test_retrieve_and_format_with_chunks(monkeypatch):
    chunks = [_chunk(0, "a", 0.91), _chunk(1, "b", 0.82)]
    monkeypatch.setattr(rag, "retrieve_for_query", AsyncMock(return_value=chunks))

    block, meta = await rag.retrieve_and_format(uuid.uuid4(), "hours?")

    assert block is not None and "a" in block and "b" in block
    assert meta.chunks_returned == 2
    assert meta.top_similarity == 0.91
    assert isinstance(meta.retrieval_ms, int) and meta.retrieval_ms >= 0


async def test_retrieve_and_format_no_chunks(monkeypatch):
    monkeypatch.setattr(rag, "retrieve_for_query", AsyncMock(return_value=[]))

    block, meta = await rag.retrieve_and_format(uuid.uuid4(), "off-topic")

    assert block is None
    assert meta.chunks_returned == 0
    assert meta.top_similarity is None


# --- RAGState ----------------------------------------------------------------


def test_rag_state_take_clears():
    state = rag.RAGState()
    meta = rag.RetrievalMeta(chunks_returned=1, top_similarity=0.9, retrieval_ms=5)
    state.last_meta = meta
    assert state.take() is meta
    assert state.take() is None


def test_retrieval_meta_as_dict():
    meta = rag.RetrievalMeta(chunks_returned=2, top_similarity=0.8, retrieval_ms=12)
    assert meta.as_dict() == {
        "chunks_returned": 2,
        "top_similarity": 0.8,
        "retrieval_ms": 12,
    }
