"""Tenant-facing portal APIs (tickets 5.08, 5.09).

Scoped to the caller's tenant via the auth context (RLS is the DB-level backstop
for direct access)."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.errors import api_error
from app.middleware.auth import TenantContext, get_current_tenant
from app.models.portal import (
    BillingSummary,
    CallDetail,
    CallListPage,
    ConsentDisclosure,
    DashboardSummary,
)
from app.services.consent import get_consent_disclosure
from app.services.portal_billing import get_billing_summary
from app.services.portal_call_detail import get_call_detail
from app.services.portal_calls import list_tenant_calls
from app.services.portal_dashboard import get_dashboard_summary

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
