from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.db.supabase import get_service_role_client
from app.middleware.auth import InternalUserContext, require_internal_user
from app.services.audit import log_internal_action
from app.services.metrics import latency_percentiles
from app.services.voice import agent_registry

router = APIRouter(prefix="/internal", tags=["internal"])


class InternalPingResponse(BaseModel):
    status: str
    internal_role: str
    tenant_count: int


class LatencyPercentile(BaseModel):
    p50: int | None = None
    p95: int | None = None
    p99: int | None = None


class LatencyStatsResponse(BaseModel):
    sample_size: int
    stt_ms: LatencyPercentile
    llm_ms: LatencyPercentile
    tts_first_byte_ms: LatencyPercentile
    total_ms: LatencyPercentile


class ActiveAgent(BaseModel):
    call_sid: str
    age_secs: int


class ActiveAgentsResponse(BaseModel):
    active_count: int
    agents: list[ActiveAgent]


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


@router.get(
    "/latency",
    response_model=LatencyStatsResponse,
    summary="Per-turn latency percentiles",
    description=(
        "Requires an authenticated internal user. Returns p50/p95/p99 for each "
        "latency segment (STT, LLM, TTS first byte, total) over the most recent "
        "100 assistant turns (ticket 2.15)."
    ),
)
async def internal_latency(
    ctx: Annotated[InternalUserContext, Depends(require_internal_user)],
) -> LatencyStatsResponse:
    stats = await latency_percentiles()
    return LatencyStatsResponse(**stats)


@router.get(
    "/agents",
    response_model=ActiveAgentsResponse,
    summary="Active voice agents",
    description=(
        "Requires an authenticated internal user. Returns the count and ages of "
        "currently running pipeline agents (ticket 2.18)."
    ),
)
async def internal_agents(
    ctx: Annotated[InternalUserContext, Depends(require_internal_user)],
) -> ActiveAgentsResponse:
    return ActiveAgentsResponse(
        active_count=agent_registry.active_count(),
        agents=[ActiveAgent(**agent) for agent in agent_registry.list_active()],
    )
