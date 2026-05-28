from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StarterPrompt(StrEnum):
    RECEPTIONIST = "receptionist"
    RESTAURANT = "restaurant"
    HOTEL = "hotel"
    RETAIL = "retail"
    GENERIC_SUPPORT = "generic_support"


class Agent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    starter_prompt: StarterPrompt
    system_prompt: str
    tools: list[str] = Field(default_factory=list)
    voice_id: str
    phone_number: str
    twilio_sid: str
    is_active: bool = True
    version: int = 1
    archived_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
