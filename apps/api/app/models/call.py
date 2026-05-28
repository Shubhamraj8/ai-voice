from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CallOutcome(StrEnum):
    BOOKED = "booked"
    TRANSFERRED = "transferred"
    INFO_ONLY = "info_only"
    ABANDONED = "abandoned"


class Call(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    agent_id: UUID
    twilio_call_sid: str
    from_number: str
    started_at: datetime
    ended_at: datetime | None = None
    duration_secs: int | None = None
    recording_url: str | None = None
    summary: str | None = None
    outcome: CallOutcome | None = None
    cost_usd: Decimal | None = None
    provider_snapshot: dict[str, Any] | None = None


class CallCreate(BaseModel):
    tenant_id: UUID
    agent_id: UUID
    twilio_call_sid: str = Field(min_length=1)
    from_number: str = Field(min_length=1)
