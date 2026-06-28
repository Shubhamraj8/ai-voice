"""Internal cross-tenant calls viewer (staff troubleshooting)."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.middleware.auth import InternalUserContext, require_internal_user
from app.services.internal_calls import list_all_calls

router = APIRouter(prefix="/internal/calls", tags=["internal-calls"])


class InternalCallRow(BaseModel):
    id: UUID
    tenant_id: UUID
    tenant_name: str
    from_number: str | None = None
    started_at: datetime
    duration_secs: int | None = None
    outcome: str | None = None
    intent: str | None = None


class InternalCallsPage(BaseModel):
    items: list[InternalCallRow]
    total: int
    page: int
    page_size: int


@router.get("", response_model=InternalCallsPage)
async def get_internal_calls(
    _ctx: Annotated[InternalUserContext, Depends(require_internal_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    tenant: UUID | None = None,
    outcome: str | None = None,
) -> InternalCallsPage:
    total, rows = await list_all_calls(
        page=page, page_size=page_size, tenant_id=tenant, outcome=outcome
    )
    return InternalCallsPage(
        items=[InternalCallRow(**row) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
    )
