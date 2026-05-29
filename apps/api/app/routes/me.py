from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.middleware.auth import (
    TenantContext,
    User,
    get_current_tenant,
    get_current_user,
)
from app.models.tenant import Tenant
from app.models.user import TenantUserRole

router = APIRouter(tags=["me"])


class MeResponse(BaseModel):
    user: User
    tenant: Tenant
    role: TenantUserRole


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Get current user and tenant context",
    description=(
        "Returns the currently authenticated user, their active tenant, "
        "and their role within that tenant."
    ),
)
async def get_me(
    user: Annotated[User, Depends(get_current_user)],
    tenant_context: Annotated[TenantContext, Depends(get_current_tenant)],
) -> MeResponse:
    return MeResponse(
        user=user,
        tenant=tenant_context.tenant,
        role=tenant_context.role,
    )
