import struct
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from app.db.supabase import get_service_role_client
from app.middleware.auth import InternalUserContext, require_internal_user
from app.providers.deepgram_tts import VOICE_CATALOGUE, DeepgramTTS
from app.services.agent_internal import validate_voice_id
from app.services.audit import log_internal_action
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
