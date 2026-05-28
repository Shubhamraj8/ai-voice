from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TenantUserRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class TenantUser(BaseModel):
    """Tenant membership row (tenant_users). Ticket name: User."""

    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID
    user_id: UUID
    role: TenantUserRole
    created_at: datetime
