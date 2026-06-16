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
    uploaded_at: datetime
    processed_at: datetime | None = None
