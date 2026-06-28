import struct
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel

from app.db.pool import get_pool
from app.db.supabase import get_service_role_client
from app.middleware.auth import InternalUserContext, require_internal_user
from app.models.internal_tenant import AuditLogListResponse
from app.providers.deepgram_tts import VOICE_CATALOGUE, DeepgramTTS
from app.services.agent_internal import validate_voice_id
from app.services.audit import log_internal_action
from app.services.audit_query import list_audit_log
from app.services.internal_metrics import platform_metrics
from app.services.metrics import latency_percentiles
from app.services.voice import agent_registry

router = APIRouter(prefix="/internal", tags=["internal"])

# Sample line spoken by the voice-preview endpoint (ticket 3.08).
VOICE_PREVIEW_LINE = "Hello! Thanks for calling. How can I help you today?"


def _pcm16_to_wav(pcm: bytes, *, sample_rate: int = 8000) -> bytes:
    """Wrap raw 16-bit mono PCM in a WAV header so a browser can play it."""

    channels, bits = 1, 16
    byte_rate = sample_rate * channels * bits // 8
    block_align = channels * bits // 8
    return (
        b"RIFF"
        + struct.pack("<I", 36 + len(pcm))
        + b"WAVE"
        + b"fmt "
        + struct.pack(
            "<IHHIIHH", 16, 1, channels, sample_rate, byte_rate, block_align, bits
        )
        + b"data"
        + struct.pack("<I", len(pcm))
        + pcm
    )


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


class TenantCounts(BaseModel):
    total: int
    active: int
    paused: int
    churned: int


class CallCounts(BaseModel):
    total: int
    last_24h: int


class PlatformMetricsResponse(BaseModel):
    tenants: TenantCounts
    calls: CallCounts
    minutes_total: float
    latency: LatencyStatsResponse


class ActiveAgent(BaseModel):
    call_sid: str
    age_secs: int


class ActiveAgentsResponse(BaseModel):
    active_count: int
    agents: list[ActiveAgent]


class VoiceCatalogResponse(BaseModel):
    voices: list[str]
    default: str


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
    "/metrics",
    response_model=PlatformMetricsResponse,
    summary="Platform-wide KPIs",
    description=(
        "Requires an authenticated internal user. Tenant + call counts plus the "
        "per-turn latency percentiles for the internal metrics page."
    ),
)
async def internal_metrics(
    _ctx: Annotated[InternalUserContext, Depends(require_internal_user)],
) -> PlatformMetricsResponse:
    counts = await platform_metrics()
    stats = await latency_percentiles()
    return PlatformMetricsResponse(
        tenants=counts["tenants"],
        calls=counts["calls"],
        minutes_total=counts["minutes_total"],
        latency=LatencyStatsResponse(**stats),
    )


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


@router.get(
    "/voices",
    response_model=VoiceCatalogResponse,
    summary="Aura voice catalogue",
    description="The selectable TTS voices for agents (ticket 3.08).",
)
async def internal_voices(
    _ctx: Annotated[InternalUserContext, Depends(require_internal_user)],
) -> VoiceCatalogResponse:
    return VoiceCatalogResponse(voices=VOICE_CATALOGUE, default=VOICE_CATALOGUE[0])


@router.get(
    "/voices/{voice_id}/preview",
    summary="Voice preview audio",
    description="Synthesize a short sample line in the given voice (WAV).",
)
async def internal_voice_preview(
    voice_id: str,
    _ctx: Annotated[InternalUserContext, Depends(require_internal_user)],
) -> Response:
    validate_voice_id(voice_id)
    tts = DeepgramTTS()
    chunks = [
        chunk async for chunk in tts.synthesize(VOICE_PREVIEW_LINE, voice_id, "en")
    ]
    return Response(content=_pcm16_to_wav(b"".join(chunks)), media_type="audio/wav")


@router.get(
    "/audit",
    response_model=AuditLogListResponse,
    summary="Audit log viewer",
    description=(
        "Requires an authenticated internal user. Paginated, newest-first audit "
        "log with composable filters (ticket 3.12)."
    ),
)
async def internal_audit(
    _ctx: Annotated[InternalUserContext, Depends(require_internal_user)],
    pool=Depends(get_pool),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    actor_type: str | None = None,
    action: str | None = None,
    target_type: str | None = None,
    tenant: UUID | None = None,
    search: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> AuditLogListResponse:
    async with pool.acquire() as conn:
        return await list_audit_log(
            conn,
            page=page,
            page_size=page_size,
            actor_type=actor_type,
            action=action,
            target_type=target_type,
            tenant_id=tenant,
            search=search,
            date_from=date_from,
            date_to=date_to,
        )
