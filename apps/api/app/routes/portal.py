"""Tenant-facing portal APIs (tickets 5.08, 5.09).

Scoped to the caller's tenant via the auth context (RLS is the DB-level backstop
for direct access)."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.config import get_settings
from app.db.pool import get_pool
from app.errors import api_error
from app.middleware.auth import (
    TenantContext,
    User,
    get_current_tenant,
    get_current_user,
)
from app.models.portal import (
    BillingSummary,
    CallDetail,
    CallListPage,
    ConsentDisclosure,
    DashboardSummary,
)
from app.services.audit import log_tenant_action
from app.services.consent import get_consent_disclosure
from app.services.portal_billing import get_billing_summary
from app.services.portal_call_detail import get_call_detail
from app.services.portal_calls import list_tenant_calls
from app.services.portal_dashboard import get_dashboard_summary
from app.services.twilio_calls import place_outbound_call


class OutboundCallRequest(BaseModel):
    to_number: str


router = APIRouter(prefix="/portal", tags=["portal"])


@router.get("/dashboard", response_model=DashboardSummary)
async def get_portal_dashboard(
    tenant_context: Annotated[TenantContext, Depends(get_current_tenant)],
) -> DashboardSummary:
    return await get_dashboard_summary(tenant_context.tenant)


@router.get("/calls", response_model=CallListPage)
async def get_portal_calls(
    tenant_context: Annotated[TenantContext, Depends(get_current_tenant)],
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    outcome: str | None = None,
    intent: str | None = None,
    search: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> CallListPage:
    return await list_tenant_calls(
        tenant_context.tenant.id,
        page=page,
        page_size=page_size,
        outcome=outcome,
        intent=intent,
        search=search,
        date_from=date_from,
        date_to=date_to,
    )


@router.post("/calls/outbound", status_code=202)
async def place_portal_outbound_call(
    body: OutboundCallRequest,
    user: Annotated[User, Depends(get_current_user)],
    tenant_context: Annotated[TenantContext, Depends(get_current_tenant)],
    pool=Depends(get_pool),
) -> dict:
    """Place an outbound call from the tenant's agent number to ``to_number``.

    The answered call runs the same agent pipeline as an inbound call.
    """

    tenant_id = tenant_context.tenant.id
    async with pool.acquire() as conn:
        agent = await conn.fetchrow(
            "SELECT phone_number FROM agents "
            "WHERE tenant_id = $1 AND is_active = true AND archived_at IS NULL "
            "ORDER BY created_at LIMIT 1",
            tenant_id,
        )
    if agent is None or not agent["phone_number"]:
        raise api_error(
            400, "no_agent", "No active agent is configured for this workspace."
        )

    base = get_settings().public_api_base_url.rstrip("/")
    sid = await place_outbound_call(
        to_number=body.to_number,
        from_number=agent["phone_number"],
        voice_url=f"{base}/webhooks/twilio/voice",
        status_callback_url=f"{base}/webhooks/twilio/status",
    )
    if sid is None:
        raise api_error(502, "call_failed", "Could not place the call. Try again.")

    await log_tenant_action(
        user.id,
        "portal.call.outbound",
        tenant_id=tenant_id,
        payload={"to": body.to_number, "call_sid": sid},
    )
    return {"status": "calling", "call_sid": sid}


@router.get("/billing", response_model=BillingSummary)
async def get_portal_billing(
    tenant_context: Annotated[TenantContext, Depends(get_current_tenant)],
) -> BillingSummary:
    return await get_billing_summary(tenant_context.tenant)


@router.get("/consent", response_model=ConsentDisclosure)
async def get_portal_consent(
    tenant_context: Annotated[TenantContext, Depends(get_current_tenant)],
) -> ConsentDisclosure:
    return await get_consent_disclosure(tenant_context.tenant.id)


@router.get("/calls/{call_id}", response_model=CallDetail)
async def get_portal_call_detail(
    call_id: UUID,
    tenant_context: Annotated[TenantContext, Depends(get_current_tenant)],
) -> CallDetail:
    detail = await get_call_detail(tenant_context.tenant.id, call_id)
    if detail is None:
        raise api_error(404, "call_not_found", "Call not found")
    return detail
