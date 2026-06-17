"""RAG retrieval + context-injection logic (ticket 4.06).

Pure, pipecat-free so it can be unit-tested without importing the voice stack.
The Pipecat ``FrameProcessor`` that calls into this lives in ``rag_processor``.

On each user turn we embed the latest utterance, retrieve the tenant's most
relevant chunks, and (when any clear the threshold) inject them into the LLM
context as a single ``KNOWLEDGE`` system block, refreshed each turn. Per-turn
retrieval metrics are recorded for ``call_messages.retrieval_meta``.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from uuid import UUID

import structlog

from app.services.knowledge_retrieval import (
    DEFAULT_LIMIT,
    DEFAULT_THRESHOLD,
    RetrievedChunk,
    retrieve_for_query,
)

logger = structlog.get_logger(__name__)

# Stable prefix so the previous turn's block can be found and replaced.
KNOWLEDGE_PREFIX = "Use the following information from the business when answering:"
FALLBACK_INSTRUCTION = (
    "If the answer is not in this context, say you don't know and offer to "
    "transfer the call."
)


@dataclass(frozen=True)
class RetrievalMeta:
    chunks_returned: int
    top_similarity: float | None
    retrieval_ms: int

    def as_dict(self) -> dict[str, object]:
        return {
            "chunks_returned": self.chunks_returned,
            "top_similarity": self.top_similarity,
            "retrieval_ms": self.retrieval_ms,
        }


class RAGState:
    """Carries the latest turn's retrieval metrics from the injection processor
    to the turn logger (which persists it on the assistant turn)."""

    def __init__(self) -> None:
        self.last_meta: RetrievalMeta | None = None

    def take(self) -> RetrievalMeta | None:
        meta = self.last_meta
        self.last_meta = None
        return meta


def format_knowledge_block(chunks: list[RetrievedChunk]) -> str:
    body = "\n\n".join(chunk.content for chunk in chunks)
    return f"{KNOWLEDGE_PREFIX}\n\n{body}\n\n{FALLBACK_INSTRUCTION}"


def latest_user_query(messages: list[dict]) -> str | None:
    """Return the most recent non-empty user-message text, or None."""

    for message in reversed(messages):
        if message.get("role") != "user":
            continue
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content
    return None


def inject_knowledge(messages: list[dict], block: str) -> list[dict]:
    """Return ``messages`` with any prior KNOWLEDGE block removed and ``block``
    inserted as a system message just before the last user message."""

    cleaned = [
        message
        for message in messages
        if not (
            message.get("role") == "system"
            and isinstance(message.get("content"), str)
            and message["content"].startswith(KNOWLEDGE_PREFIX)
        )
    ]
    knowledge_message = {"role": "system", "content": block}

    for index in range(len(cleaned) - 1, -1, -1):
        if cleaned[index].get("role") == "user":
            cleaned.insert(index, knowledge_message)
            return cleaned

    cleaned.append(knowledge_message)
    return cleaned


async def retrieve_and_format(
    tenant_id: UUID,
    query: str,
    *,
    threshold: float = DEFAULT_THRESHOLD,
    limit: int = DEFAULT_LIMIT,
) -> tuple[str | None, RetrievalMeta]:
    """Retrieve chunks for ``query`` and build the KNOWLEDGE block (or None when
    nothing clears the threshold), plus per-turn retrieval metrics."""

    start = time.monotonic()
    chunks = await retrieve_for_query(
        tenant_id, query, threshold=threshold, limit=limit
    )
    retrieval_ms = round((time.monotonic() - start) * 1000)

    top_similarity = max((c.similarity for c in chunks), default=None)
    meta = RetrievalMeta(
        chunks_returned=len(chunks),
        top_similarity=top_similarity,
        retrieval_ms=retrieval_ms,
    )
    block = format_knowledge_block(chunks) if chunks else None
    return block, meta
