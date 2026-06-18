from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# Basic email shape check — avoids the email-validator dependency.
_EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

LeadStatus = Literal["new", "contacted", "converted", "lost"]


class LeadCreate(BaseModel):
    """Public lead-capture form payload."""

    contact_email: str = Field(min_length=3, max_length=320, pattern=_EMAIL_PATTERN)
    business_name: str | None = Field(default=None, max_length=200)
    contact_name: str | None = Field(default=None, max_length=200)
    contact_phone: str | None = Field(default=None, max_length=32)
    message: str | None = Field(default=None, max_length=2000)
    source: str | None = Field(default=None, max_length=100)


class Lead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_name: str | None = None
    contact_name: str | None = None
    contact_email: str
    contact_phone: str | None = None
    message: str | None = None
    source: str | None = None
    status: str
    created_at: datetime


class LeadStatusUpdate(BaseModel):
    status: LeadStatus
