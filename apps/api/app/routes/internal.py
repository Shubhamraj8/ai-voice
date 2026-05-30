from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.db.supabase import get_service_role_client
from app.middleware.auth import InternalUserContext, require_internal_user
from app.services.audit import log_internal_action

router = APIRouter(prefix="/internal", tags=["internal"])


class InternalPingResponse(BaseModel):
    status: str
    internal_role: str
    tenant_count: int


@router.get(
    "/ping",
    response_model=InternalPingResponse,
    summary="Internal team health check",
    description=(
        "Requires an authenticated internal user. "
        "Uses the service-role client for a cross-tenant read (RLS bypass)."
    ),
)
async def internal_ping(
    ctx: Annotated[InternalUserContext, Depends(require_internal_user)],
) -> InternalPingResponse:
    client = get_service_role_client()
    result = client.table("tenants").select("id", count="exact").execute()
    tenant_count = result.count if result.count is not None else len(result.data or [])

    await log_internal_action(
        actor_id=ctx.user.id,
        action="internal.ping",
        payload={"tenant_count": tenant_count},
    )

    return InternalPingResponse(
        status="ok",
        internal_role=ctx.internal_role,
        tenant_count=tenant_count,
    )
