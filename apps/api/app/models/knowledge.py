from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class KnowledgeDocument(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    agent_id: UUID | None = None
    filename: str
    storage_path: str
    bytes: int
    sha256: str
    status: str
    error: str | None = None
    chunk_count: int | None = None
    uploaded_at: datetime
    processed_at: datetime | None = None


class KnowledgeDocumentDetail(KnowledgeDocument):
    """Document plus ingestion progress (ticket 4.02)."""

    chunks_total: int | None = None  # known once chunking completes
    chunks_done: int = 0  # embeddings written so far


class KnowledgeChunk(BaseModel):
    """A sample chunk for the dashboard detail drawer (ticket 4.15)."""

    chunk_index: int
    content: str
    token_count: int | None = None
