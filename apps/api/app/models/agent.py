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


# Max length keeps prompt assembly + LLM context bounded (ticket 3.07).
MAX_SYSTEM_PROMPT_CHARS = 4000


class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    starter_prompt: StarterPrompt = StarterPrompt.RECEPTIONIST
    system_prompt: str = Field(min_length=1, max_length=MAX_SYSTEM_PROMPT_CHARS)
    voice_id: str = Field(min_length=1)
    phone_number: str = Field(min_length=1)
    twilio_sid: str = Field(min_length=1)
    tools: list[str] = Field(default_factory=list)


class AgentPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    system_prompt: str | None = Field(
        default=None, min_length=1, max_length=MAX_SYSTEM_PROMPT_CHARS
    )
    voice_id: str | None = Field(default=None, min_length=1)
    tools: list[str] | None = None
    is_active: bool | None = None
