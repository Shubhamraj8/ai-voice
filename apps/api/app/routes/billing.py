"""Tenant-facing billing read API (ticket 5.07).

Powers the portal billing page (5.11). Events are scoped to the caller's tenant
via the auth context (RLS is the DB-level backstop for direct access)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.middleware.auth import TenantContext, get_current_tenant
from app.models.billing import BillingEvent
from app.services.billing import list_billing_events

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/events", response_model=list[BillingEvent])
async def get_billing_events(
    tenant_context: Annotated[TenantContext, Depends(get_current_tenant)],
    event_type: str | None = None,
    limit: int = Query(100, ge=1, le=500),
) -> list[BillingEvent]:
    return await list_billing_events(
        tenant_context.tenant.id, event_type=event_type, limit=limit
    )
