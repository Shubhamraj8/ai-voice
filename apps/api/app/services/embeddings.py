"""OpenAI text embeddings (tickets 4.03, 4.05).

A thin wrapper over ``text-embedding-3-small`` (1536 dims) used both to embed
ingested document chunks (4.03) and to embed a caller's query at retrieval time
(4.05). The OpenAI client is created lazily so the app boots without a key set;
calls raise only when an embedding is actually requested.
"""

from __future__ import annotations

import asyncio
import math

import structlog

from app.config import get_settings, selected_embedding_provider

logger = structlog.get_logger(__name__)

EMBEDDING_DIM = 1536


def _client():
    # Lazy import + construction: openai is optional at boot, required at call time.
    from openai import AsyncOpenAI

    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    return AsyncOpenAI(api_key=settings.openai_api_key)


def _normalize(vector: list[float]) -> list[float]:
    """L2-normalize — Gemini truncated dims (output < 3072) aren't normalized."""
    norm = math.sqrt(sum(x * x for x in vector)) or 1.0
    return [x / norm for x in vector]


async def _embed_gemini(texts: list[str], task_type: str) -> list[list[float]]:
    from google import genai
    from google.genai import types

    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    client = genai.Client(api_key=settings.gemini_api_key)

    def _call():
        return client.models.embed_content(
            model=settings.gemini_embedding_model,
            contents=texts,
            config=types.EmbedContentConfig(
                output_dimensionality=EMBEDDING_DIM,
                task_type=task_type,
            ),
        )

    resp = await asyncio.to_thread(_call)
    return [_normalize(list(e.values)) for e in resp.embeddings]


async def embed_texts(
    texts: list[str], *, task_type: str = "RETRIEVAL_DOCUMENT"
) -> list[list[float]]:
    """Embed a batch of strings, preserving order. Empty input → empty list.

    ``task_type`` tunes the Gemini path (RETRIEVAL_DOCUMENT vs RETRIEVAL_QUERY);
    it is ignored by OpenAI.
    """

    if not texts:
        return []

    if selected_embedding_provider(get_settings()) == "gemini":
        return await _embed_gemini(texts, task_type)

    model = get_settings().openai_embedding_model
    resp = await _client().embeddings.create(model=model, input=texts)
    # OpenAI returns items with an .index; sort to be safe before stripping it.
    items = sorted(resp.data, key=lambda d: d.index)
    return [item.embedding for item in items]


async def embed_text(
    text: str, *, task_type: str = "RETRIEVAL_DOCUMENT"
) -> list[float]:
    """Embed a single string."""

    vectors = await embed_texts([text], task_type=task_type)
    return vectors[0]


def to_vector_literal(embedding: list[float]) -> str:
    """Format an embedding as pgvector text input: ``[0.1,0.2,...]`` (cast
    ``::vector`` in SQL). asyncpg has no native vector codec."""

    return "[" + ",".join(str(x) for x in embedding) + "]"
