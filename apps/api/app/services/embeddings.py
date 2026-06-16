"""OpenAI text embeddings (tickets 4.03, 4.05).

A thin wrapper over ``text-embedding-3-small`` (1536 dims) used both to embed
ingested document chunks (4.03) and to embed a caller's query at retrieval time
(4.05). The OpenAI client is created lazily so the app boots without a key set;
calls raise only when an embedding is actually requested.
"""

from __future__ import annotations

import structlog

from app.config import get_settings

logger = structlog.get_logger(__name__)

EMBEDDING_DIM = 1536


def _client():
    # Lazy import + construction: openai is optional at boot, required at call time.
    from openai import AsyncOpenAI

    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    return AsyncOpenAI(api_key=settings.openai_api_key)


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of strings, preserving order. Empty input → empty list."""

    if not texts:
        return []

    model = get_settings().openai_embedding_model
    resp = await _client().embeddings.create(model=model, input=texts)
    # OpenAI returns items with an .index; sort to be safe before stripping it.
    items = sorted(resp.data, key=lambda d: d.index)
    return [item.embedding for item in items]


async def embed_text(text: str) -> list[float]:
    """Embed a single string."""

    vectors = await embed_texts([text])
    return vectors[0]
