"""Tenant-facing DPDP data rights endpoints (ticket 5.12).

Scoped to the caller's tenant via the auth context."""

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.middleware.auth import (
    TenantContext,
    User,
    get_current_tenant,
    get_current_user,
)
from app.services.audit import log_tenant_action
from app.services.dpdp_delete import confirm_deletion, request_deletion
from app.services.dpdp_export import schedule_export

router = APIRouter(prefix="/dpdp", tags=["dpdp"])


class DeletionConfirm(BaseModel):
    token: str


@router.post("/export", status_code=202)
async def request_dpdp_export(
    user: Annotated[User, Depends(get_current_user)],
    tenant_context: Annotated[TenantContext, Depends(get_current_tenant)],
) -> dict:
    """Kick off a full data export; emailed to the requester as a 7-day link."""

    export_id = uuid4()
    tenant_id = tenant_context.tenant.id

    await log_tenant_action(
        user.id,
        "dpdp.export.requested",
        tenant_id=tenant_id,
        target_type="export",
        target_id=export_id,
        payload={"export_id": str(export_id)},
    )
    schedule_export(tenant_id, export_id, recipient_email=user.email)

    return {"export_id": str(export_id), "status": "processing"}


@router.post("/delete", status_code=202)
async def request_account_deletion(
    user: Annotated[User, Depends(get_current_user)],
    tenant_context: Annotated[TenantContext, Depends(get_current_tenant)],
) -> dict:
    """Start the erasure flow: emails the tenant a one-time confirmation link."""

    tenant_id = tenant_context.tenant.id
    result = await request_deletion(
        tenant_id, requested_by=user.id, recipient_email=user.email
    )
    await log_tenant_action(
        user.id,
        "dpdp.deletion.requested",
        tenant_id=tenant_id,
        target_type="tenant",
        target_id=tenant_id,
    )
    return result


@router.post("/delete/confirm", status_code=202)
async def confirm_account_deletion(body: DeletionConfirm) -> dict:
    """Confirm deletion via the emailed token (no auth — the token is the proof)."""

    return await confirm_deletion(body.token)
