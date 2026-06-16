"""Tenant-scoped knowledge retrieval (ticket 4.05).

Embeds a caller's query (caching the embedding in Redis for 5 minutes so repeated
phrasings don't re-hit OpenAI) and runs the ``retrieve_knowledge`` SQL function
to fetch the top-K most similar chunks for one tenant. Used by RAG injection in
the pipeline (ticket 4.06).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from uuid import UUID

import structlog

from app.config import get_settings
from app.db.pool import get_pool
from app.services import cache
from app.services.embeddings import embed_text

logger = structlog.get_logger(__name__)

DEFAULT_THRESHOLD = 0.7
DEFAULT_LIMIT = 5


@dataclass(frozen=True)
class RetrievedChunk:
    document_id: UUID
    chunk_index: int
    content: str
    similarity: float


def _cache_key(query: str) -> str:
    model = get_settings().openai_embedding_model
    digest = hashlib.sha1(query.strip().encode("utf-8")).hexdigest()
    return f"emb:{model}:{digest}"


def _to_vector_literal(embedding: list[float]) -> str:
    # pgvector text input form: "[0.1,0.2,...]" (cast to ::vector in SQL).
    return "[" + ",".join(str(x) for x in embedding) + "]"


async def _embed_query_cached(query: str) -> list[float]:
    key = _cache_key(query)
    cached = await cache.get_json(key)
    if isinstance(cached, list) and cached:
        return cached

    embedding = await embed_text(query)
    await cache.set_json(key, embedding, ttl_s=get_settings().embedding_cache_ttl_s)
    return embedding


async def retrieve_for_query(
    tenant_id: UUID,
    query_text: str,
    *,
    threshold: float = DEFAULT_THRESHOLD,
    limit: int = DEFAULT_LIMIT,
) -> list[RetrievedChunk]:
    """Return up to ``limit`` chunks for ``tenant_id`` above the similarity
    ``threshold``, most similar first. Empty query → no chunks."""

    if not query_text or not query_text.strip():
        return []

    embedding = await _embed_query_cached(query_text)
    vector_literal = _to_vector_literal(embedding)

    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT document_id, chunk_index, content, similarity "
            "FROM retrieve_knowledge($1, $2::vector, $3, $4)",
            tenant_id,
            vector_literal,
            threshold,
            limit,
        )

    chunks = [
        RetrievedChunk(
            document_id=row["document_id"],
            chunk_index=row["chunk_index"],
            content=row["content"],
            similarity=row["similarity"],
        )
        for row in rows
    ]
    logger.info(
        "knowledge_retrieved",
        tenant_id=str(tenant_id),
        chunks=len(chunks),
        threshold=threshold,
    )
    return chunks
