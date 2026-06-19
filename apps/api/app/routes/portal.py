"""Tenant-facing portal APIs (ticket 5.08).

Scoped to the caller's tenant via the auth context (RLS is the DB-level backstop
for direct access)."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.middleware.auth import TenantContext, get_current_tenant
from app.models.portal import DashboardSummary
from app.services.portal_dashboard import get_dashboard_summary

router = APIRouter(prefix="/portal", tags=["portal"])


@router.get("/dashboard", response_model=DashboardSummary)
async def get_portal_dashboard(
    tenant_context: Annotated[TenantContext, Depends(get_current_tenant)],
) -> DashboardSummary:
    return await get_dashboard_summary(tenant_context.tenant)
