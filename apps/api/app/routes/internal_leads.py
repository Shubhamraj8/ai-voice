"""Internal leads inbox (ticket 5.02) — list + triage captured leads."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.middleware.auth import InternalUserContext, require_internal_user
from app.models.leads import Lead, LeadStatusUpdate
from app.services.audit import log_internal_action
from app.services.leads import list_leads, update_lead_status

router = APIRouter(prefix="/internal/leads", tags=["internal-leads"])


@router.get("", response_model=list[Lead])
async def get_leads(
    _ctx: Annotated[InternalUserContext, Depends(require_internal_user)],
    status: str | None = None,
) -> list[Lead]:
    return await list_leads(status=status)


@router.patch("/{lead_id}", response_model=Lead)
async def patch_lead(
    lead_id: UUID,
    body: LeadStatusUpdate,
    ctx: Annotated[InternalUserContext, Depends(require_internal_user)],
) -> Lead:
    lead = await update_lead_status(lead_id, body.status)
    await log_internal_action(
        actor_id=ctx.user.id,
        action="internal.lead.update",
        target_type="lead",
        target_id=lead_id,
        payload={"status": body.status},
    )
    return lead
