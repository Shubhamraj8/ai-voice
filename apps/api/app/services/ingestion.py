"""Knowledge-document ingestion (ticket 4.03).

Background job that turns an uploaded PDF into searchable vectors: download from
storage, extract text (pdfplumber), chunk it (tiktoken, 500-token windows with
50-token overlap), embed the chunks (OpenAI, batched), and write them to
``knowledge_embeddings``. The document's ``status`` walks ``pending →
processing → ready`` (or ``error`` with a message). Re-running on the same
document replaces its chunks rather than duplicating them.

CPU-bound steps (pdfplumber, tiktoken) run in a worker thread so they don't
block the event loop. Triggered as a FastAPI background task on upload; the same
function backs the reprocess endpoint (ticket 4.02).
"""

from __future__ import annotations

import asyncio
import io
from collections import Counter
from dataclasses import dataclass
from uuid import UUID

import structlog

from app.db.pool import get_pool
from app.services.embeddings import embed_texts, to_vector_literal
from app.services.storage import download_document

logger = structlog.get_logger(__name__)

CHUNK_TOKENS = 500
CHUNK_OVERLAP = 50
EMBED_BATCH = 100
_ENCODING_NAME = "cl100k_base"

_encoding = None


@dataclass(frozen=True)
class Chunk:
    content: str
    token_count: int


def _get_encoding():
    # Lazy + cached: tiktoken downloads/loads the BPE vocab on first use.
    global _encoding
    if _encoding is None:
        import tiktoken

        _encoding = tiktoken.get_encoding(_ENCODING_NAME)
    return _encoding


def _remove_headers_footers(pages: list[list[str]]) -> list[list[str]]:
    """Drop the first/last line of each page when it repeats across most pages
    (running headers/footers). Needs a few pages to have any signal."""

    if len(pages) < 3:
        return pages

    tops = Counter(p[0] for p in pages if p)
    bottoms = Counter(p[-1] for p in pages if p)
    threshold = max(2, len(pages) // 2)
    repeated = {line for line, n in (tops + bottoms).items() if n >= threshold}
    if not repeated:
        return pages

    return [[line for line in p if line not in repeated] for p in pages]


def extract_text(pdf_bytes: bytes) -> str:
    """Extract text from a PDF, dropping empty pages and running headers/footers."""

    import pdfplumber

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        raw_pages = [(page.extract_text() or "") for page in pdf.pages]

    pages: list[list[str]] = []
    for raw in raw_pages:
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        if lines:
            pages.append(lines)

    pages = _remove_headers_footers(pages)
    return "\n".join("\n".join(p) for p in pages if p)


def chunk_text(
    text: str,
    *,
    chunk_tokens: int = CHUNK_TOKENS,
    overlap: int = CHUNK_OVERLAP,
) -> list[Chunk]:
    """Split ``text`` into overlapping token windows."""

    if not text.strip():
        return []

    enc = _get_encoding()
    tokens = enc.encode(text)
    step = chunk_tokens - overlap
    chunks: list[Chunk] = []
    for start in range(0, len(tokens), step):
        window = tokens[start : start + chunk_tokens]
        content = enc.decode(window).strip()
        if content:
            chunks.append(Chunk(content=content, token_count=len(window)))
        if start + chunk_tokens >= len(tokens):
            break
    return chunks


async def _embed_in_batches(chunks: list[Chunk]) -> list[list[float]]:
    embeddings: list[list[float]] = []
    for i in range(0, len(chunks), EMBED_BATCH):
        batch = chunks[i : i + EMBED_BATCH]
        embeddings.extend(await embed_texts([c.content for c in batch]))
    return embeddings


async def _set_status(
    document_id: UUID, status: str, *, error: str | None = None
) -> None:
    pool = get_pool()
    async with pool.acquire() as conn:
        if status == "ready":
            await conn.execute(
                "UPDATE knowledge_documents "
                "SET status='ready', error=NULL, processed_at=now() WHERE id=$1",
                document_id,
            )
        else:
            await conn.execute(
                "UPDATE knowledge_documents SET status=$2, error=$3 WHERE id=$1",
                document_id,
                status,
                error,
            )


async def process_document(document_id: UUID) -> None:
    """Ingest one document end-to-end. Never raises — failures are recorded on
    the row as ``status='error'`` so the upload request stays unaffected."""

    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT tenant_id, storage_path FROM knowledge_documents WHERE id=$1",
            document_id,
        )
    if row is None:
        logger.warning("ingest_document_missing", document_id=str(document_id))
        return

    tenant_id = row["tenant_id"]
    storage_path = row["storage_path"]
    await _set_status(document_id, "processing")

    try:
        # storage_path is "{bucket}/{tenant}/{doc}.pdf"; strip the bucket prefix.
        object_path = (
            storage_path.split("/", 1)[1] if "/" in storage_path else storage_path
        )
        pdf_bytes = await download_document(path=object_path)
        if not pdf_bytes:
            raise RuntimeError("could not download document from storage")

        text = await asyncio.to_thread(extract_text, pdf_bytes)
        chunks = await asyncio.to_thread(chunk_text, text)
        if not chunks:
            raise RuntimeError("no extractable text in document")

        embeddings = await _embed_in_batches(chunks)
        total_tokens = sum(c.token_count for c in chunks)

        rows = [
            (
                tenant_id,
                document_id,
                idx,
                chunk.content,
                chunk.token_count,
                to_vector_literal(vector),
            )
            for idx, (chunk, vector) in enumerate(zip(chunks, embeddings))
        ]

        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "DELETE FROM knowledge_embeddings WHERE document_id=$1",
                    document_id,
                )
                await conn.executemany(
                    "INSERT INTO knowledge_embeddings "
                    "(tenant_id, document_id, chunk_index, content, token_count, "
                    "embedding) VALUES ($1, $2, $3, $4, $5, $6::vector)",
                    rows,
                )
                await conn.execute(
                    "UPDATE knowledge_documents "
                    "SET status='ready', error=NULL, processed_at=now() WHERE id=$1",
                    document_id,
                )

        logger.info(
            "ingest_document_ready",
            document_id=str(document_id),
            tenant_id=str(tenant_id),
            chunks=len(chunks),
            tokens=total_tokens,
        )
    except Exception as exc:
        logger.error(
            "ingest_document_failed", document_id=str(document_id), error=str(exc)
        )
        await _set_status(document_id, "error", error=str(exc)[:500])
