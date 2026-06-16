"""Tests for tenant-scoped knowledge retrieval (ticket 4.05).

OpenAI, Redis, and the DB are all mocked — no embeddings are computed and no
SQL runs.
"""

import uuid
from unittest.mock import AsyncMock

from app.services import knowledge_retrieval as kr


def _chunk_row(idx: int, similarity: float):
    return {
        "document_id": uuid.uuid4(),
        "chunk_index": idx,
        "content": f"chunk {idx}",
        "similarity": similarity,
    }


# --- pure helpers ------------------------------------------------------------


def test_to_vector_literal_format():
    assert kr._to_vector_literal([0.1, 0.2, 0.3]) == "[0.1,0.2,0.3]"


def test_cache_key_strips_and_is_deterministic():
    assert kr._cache_key("  hello  ") == kr._cache_key("hello")
    assert kr._cache_key("a") != kr._cache_key("b")


# --- retrieve_for_query ------------------------------------------------------


async def test_empty_query_returns_no_chunks(monkeypatch):
    embed = AsyncMock()
    monkeypatch.setattr(kr, "embed_text", embed)

    assert await kr.retrieve_for_query(uuid.uuid4(), "   ") == []
    embed.assert_not_awaited()


async def test_cache_miss_embeds_caches_and_queries(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    embedding = [0.01] * 1536
    conn.fetch.return_value = [_chunk_row(0, 0.92), _chunk_row(1, 0.81)]

    monkeypatch.setattr(kr, "get_pool", lambda: pool)
    monkeypatch.setattr(kr.cache, "get_json", AsyncMock(return_value=None))
    set_json = AsyncMock()
    monkeypatch.setattr(kr.cache, "set_json", set_json)
    embed = AsyncMock(return_value=embedding)
    monkeypatch.setattr(kr, "embed_text", embed)

    chunks = await kr.retrieve_for_query(uuid.uuid4(), "what are your hours?")

    assert [c.chunk_index for c in chunks] == [0, 1]
    assert chunks[0].similarity == 0.92
    embed.assert_awaited_once()
    set_json.assert_awaited_once()
    # The query was passed to the SQL function with a ::vector literal.
    args = conn.fetch.await_args.args
    assert args[2] == kr._to_vector_literal(embedding)


async def test_cache_hit_skips_embedding(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    cached = [0.02] * 1536
    conn.fetch.return_value = [_chunk_row(0, 0.88)]

    monkeypatch.setattr(kr, "get_pool", lambda: pool)
    monkeypatch.setattr(kr.cache, "get_json", AsyncMock(return_value=cached))
    set_json = AsyncMock()
    monkeypatch.setattr(kr.cache, "set_json", set_json)
    embed = AsyncMock()
    monkeypatch.setattr(kr, "embed_text", embed)

    chunks = await kr.retrieve_for_query(uuid.uuid4(), "hours?")

    assert len(chunks) == 1
    embed.assert_not_awaited()
    set_json.assert_not_awaited()


async def test_threshold_and_limit_passed_through(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    conn.fetch.return_value = []
    monkeypatch.setattr(kr, "get_pool", lambda: pool)
    monkeypatch.setattr(kr.cache, "get_json", AsyncMock(return_value=[0.0] * 1536))
    monkeypatch.setattr(kr.cache, "set_json", AsyncMock())

    tenant_id = uuid.uuid4()
    await kr.retrieve_for_query(tenant_id, "q", threshold=0.5, limit=3)

    args = conn.fetch.await_args.args
    assert args[1] == tenant_id
    assert args[3] == 0.5
    assert args[4] == 3
