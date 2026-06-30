"""Pipecat voice pipeline for Twilio Media Streams (tickets 2.04–2.12)."""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass
from typing import TYPE_CHECKING

import structlog
from fastapi import WebSocket
from pipecat.frames.frames import (
    OutputAudioRawFrame,
    TTSSpeakFrame,
)
from pipecat.observers.user_bot_latency_observer import UserBotLatencyObserver
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineParams, PipelineWorker
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.runner.utils import parse_telephony_websocket
from pipecat.serializers.twilio import TwilioFrameSerializer
from pipecat.transports.websocket.fastapi import (
    FastAPIWebsocketParams,
    FastAPIWebsocketTransport,
)
from pipecat.turns.user_turn_strategies import ExternalUserTurnStrategies
from pipecat.workers.runner import WorkerRunner

from app.config import llm_key_present, selected_llm_provider
from app.models.tenant import ProviderConfig
from app.providers.registry import ensure_live_providers
from app.services.calls import get_call_pipeline_context
from app.services.voice import agent_registry
from app.services.voice.audio_config import (
    STT_INPUT_SAMPLE_RATE,
    TTS_OUTPUT_SAMPLE_RATE,
    TWILIO_SAMPLE_RATE,
)
from app.services.voice.buffer_monitor import AudioBufferUnderrunMonitor
from app.services.voice.conversation_config import (
    GREETING_TEXT,
    MAX_LLM_OUTPUT_TOKENS,
    build_llm_context,
)
from app.services.voice.rag import RAGState
from app.services.voice.rag_processor import RAGInjectionProcessor
from app.services.voice.tools_adapter import build_tools_schema, register_tools
from app.services.voice.turn_config import (
    DEEPGRAM_ENDPOINTING_MS,
    DEEPGRAM_STT_LANGUAGE,
    DEEPGRAM_STT_MODEL,
    build_user_turn_processor,
    build_vad_processor,
)
from app.services.voice.turn_logger import (
    attach_turn_logging,
    build_turn_metrics_collector,
)
from app.tools.base import ToolContext
from app.tools.registry import registry as tool_registry

if TYPE_CHECKING:
    from uuid import UUID

    from pipecat.processors.aggregators.llm_response_universal import (
        LLMAssistantAggregator,
        LLMUserAggregator,
    )

    from app.config import Settings


logger = structlog.get_logger(__name__)


HELLO_SAMPLE_RATE = TTS_OUTPUT_SAMPLE_RATE

HELLO_DURATION_SECS = 1.2

HELLO_FREQUENCY_HZ = 523

DEEPGRAM_CONNECT_GREETING = "Audio pipeline connected."


@dataclass
class ConversationPipeline:
    """Built STT → LLM → TTS pipeline components."""

    worker: PipelineWorker
    user_aggregator: LLMUserAggregator
    assistant_aggregator: LLMAssistantAggregator
    latency_observer: UserBotLatencyObserver


def generate_hello_audio_pcm(
    *,
    sample_rate: int = HELLO_SAMPLE_RATE,
    duration_secs: float = HELLO_DURATION_SECS,
    frequency_hz: int = HELLO_FREQUENCY_HZ,
) -> bytes:
    """Generate a short PCM16 tone callers hear when providers are not configured."""

    sample_count = int(sample_rate * duration_secs)

    samples: list[int] = []

    for index in range(sample_count):
        envelope = min(1.0, index / (sample_rate * 0.05))

        sample = int(
            12000
            * math.sin(2 * math.pi * frequency_hz * index / sample_rate)
            * envelope
        )

        samples.append(sample)

    return struct.pack(f"<{len(samples)}h", *samples)


def _build_twilio_serializer(
    *,
    stream_id: str,
    call_id: str | None,
    settings: Settings,
) -> TwilioFrameSerializer:

    can_auto_hang_up = bool(
        call_id and settings.twilio_account_sid and settings.twilio_auth_token
    )

    return TwilioFrameSerializer(
        stream_sid=stream_id,
        call_sid=call_id,
        account_sid=settings.twilio_account_sid or None,
        auth_token=settings.twilio_auth_token or None,
        params=TwilioFrameSerializer.InputParams(auto_hang_up=can_auto_hang_up),
    )


def _build_transport(
    websocket: WebSocket,
    serializer: TwilioFrameSerializer,
) -> FastAPIWebsocketTransport:

    return FastAPIWebsocketTransport(
        websocket=websocket,
        params=FastAPIWebsocketParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            add_wav_header=False,
            serializer=serializer,
        ),
    )


def _build_deepgram_stt_settings():
    """Deepgram Listen settings for provider layer (2.08) and turn detection (2.10)."""

    from pipecat.services.deepgram.stt import DeepgramSTTService

    return DeepgramSTTService.Settings(
        model=DEEPGRAM_STT_MODEL,
        language=DEEPGRAM_STT_LANGUAGE,
        smart_format=True,
        endpointing=DEEPGRAM_ENDPOINTING_MS,
        interim_results=True,
        extra={"vad_events": True},
    )


def _normalize_deepseek_base_url(base_url: str) -> str:
    """Ensure the DeepSeek OpenAI-compatible client gets a ``/v1`` suffix."""

    normalized = base_url.rstrip("/")

    if normalized.endswith("/v1"):
        return normalized

    return f"{normalized}/v1"


def _build_deepseek_llm_service(settings: Settings):
    """Build Pipecat's DeepSeek LLM service from app settings (ticket 2.09)."""

    from pipecat.services.deepseek.llm import DeepSeekLLMService

    return DeepSeekLLMService(
        api_key=settings.deepseek_api_key,
        base_url=_normalize_deepseek_base_url(settings.deepseek_base_url),
        settings=DeepSeekLLMService.Settings(
            model=settings.deepseek_model,
            max_tokens=MAX_LLM_OUTPUT_TOKENS,
        ),
    )


def _build_gemini_llm_service(settings: Settings):
    """Build Pipecat's native Google Gemini LLM service (Google AI Studio)."""

    from pipecat.services.google.llm import GoogleLLMService

    return GoogleLLMService(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        params=GoogleLLMService.InputParams(
            max_tokens=MAX_LLM_OUTPUT_TOKENS,
            # Gemini 2.5 defaults to "dynamic thinking", which spends the output
            # token budget on hidden reasoning and returns an empty/truncated
            # reply at our small MAX_LLM_OUTPUT_TOKENS. Disable it so the whole
            # budget goes to the spoken answer (also lower latency for voice).
            thinking=GoogleLLMService.ThinkingConfig(thinking_budget=0),
        ),
    )


def _build_llm_service(settings: Settings):
    """Build the conversational LLM for the selected provider (DeepSeek/Gemini)."""

    if selected_llm_provider(settings) == "gemini":
        return _build_gemini_llm_service(settings)
    return _build_deepseek_llm_service(settings)


def _build_deepgram_only_pipeline(
    transport: FastAPIWebsocketTransport,
    settings: Settings,
) -> PipelineWorker:
    """STT + TTS without LLM — used when DeepSeek credentials are absent."""

    from pipecat.services.deepgram.stt import DeepgramSTTService
    from pipecat.services.deepgram.tts import DeepgramTTSService

    vad_processor = build_vad_processor(sample_rate=STT_INPUT_SAMPLE_RATE)
    user_turn_processor = build_user_turn_processor()

    stt = DeepgramSTTService(
        api_key=settings.deepgram_api_key,
        sample_rate=STT_INPUT_SAMPLE_RATE,
        settings=_build_deepgram_stt_settings(),
    )

    tts = DeepgramTTSService(
        api_key=settings.deepgram_api_key,
        sample_rate=TTS_OUTPUT_SAMPLE_RATE,
        encoding="linear16",
        settings=DeepgramTTSService.Settings(voice=settings.deepgram_voice),
    )

    buffer_monitor = AudioBufferUnderrunMonitor()

    pipeline = Pipeline(
        [
            transport.input(),
            vad_processor,
            stt,
            user_turn_processor,
            tts,
            buffer_monitor,
            transport.output(),
        ]
    )

    return PipelineWorker(
        pipeline,
        params=PipelineParams(
            audio_in_sample_rate=STT_INPUT_SAMPLE_RATE,
            audio_out_sample_rate=TTS_OUTPUT_SAMPLE_RATE,
        ),
        enable_rtvi=False,
    )


def _build_conversation_pipeline(
    transport: FastAPIWebsocketTransport,
    settings: Settings,
    *,
    call_db_id: UUID | None = None,
    tenant_id: UUID | None = None,
    agent_id: UUID | None = None,
    twilio_call_sid: str | None = None,
    voice_id: str | None = None,
    system_prompt: str | None = None,
    tool_whitelist: list[str] | None = None,
) -> ConversationPipeline:
    """Wire Deepgram STT → DeepSeek LLM → Deepgram TTS with turn detection (2.12).

    ``voice_id`` and ``system_prompt`` come from the resolved agent (3.10),
    falling back to the configured defaults.
    """

    from pipecat.services.deepgram.stt import DeepgramSTTService
    from pipecat.services.deepgram.tts import DeepgramTTSService

    vad_processor = build_vad_processor(sample_rate=STT_INPUT_SAMPLE_RATE)
    user_turn_processor = build_user_turn_processor()

    stt = DeepgramSTTService(
        api_key=settings.deepgram_api_key,
        sample_rate=STT_INPUT_SAMPLE_RATE,
        settings=_build_deepgram_stt_settings(),
    )

    llm = _build_llm_service(settings)

    tts = DeepgramTTSService(
        api_key=settings.deepgram_api_key,
        sample_rate=TTS_OUTPUT_SAMPLE_RATE,
        encoding="linear16",
        settings=DeepgramTTSService.Settings(voice=voice_id or settings.deepgram_voice),
    )

    context = build_llm_context(system_prompt)

    # Expose the agent's whitelisted (and registered) tools to the LLM (4.07).
    # Until concrete tools register (4.08+) this resolves to nothing.
    tools = tool_registry.tools_for(tool_whitelist)
    if tools:
        context.set_tools(build_tools_schema(tools))
        register_tools(
            llm,
            tools,
            ToolContext(
                tenant_id=tenant_id,
                agent_id=agent_id,
                call_id=call_db_id,
                twilio_call_sid=twilio_call_sid,
            ),
        )

    context_aggregator = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(
            user_turn_strategies=ExternalUserTurnStrategies(),
        ),
    )

    buffer_monitor = AudioBufferUnderrunMonitor()
    metrics_collector = build_turn_metrics_collector()

    @stt.event_handler("on_connected")
    async def on_stt_connected(stt_service) -> None:

        logger.info("deepgram_stt_connected")

    @stt.event_handler("on_disconnected")
    async def on_stt_disconnected(stt_service) -> None:

        logger.info("deepgram_stt_disconnected")

    @user_turn_processor.event_handler("on_user_turn_started")
    async def on_user_turn_started(processor, strategy) -> None:

        logger.info(
            "user_turn_started",
            strategy=type(strategy).__name__,
            barge_in=True,
        )

    @user_turn_processor.event_handler("on_user_turn_stopped")
    async def on_user_turn_stopped(processor, strategy) -> None:

        logger.info(
            "user_turn_stopped",
            strategy=type(strategy).__name__,
        )

    # RAG: inject the tenant's relevant knowledge into the context before the
    # LLM, on each user turn (ticket 4.06). Only when we know the tenant.
    rag_state = RAGState()
    processors = [
        transport.input(),
        vad_processor,
        stt,
        user_turn_processor,
        context_aggregator.user(),
    ]
    if tenant_id is not None:
        processors.append(RAGInjectionProcessor(tenant_id=tenant_id, state=rag_state))
    processors += [
        llm,
        tts,
        buffer_monitor,
        transport.output(),
        context_aggregator.assistant(),
    ]

    pipeline = Pipeline(processors)

    worker = PipelineWorker(
        pipeline,
        params=PipelineParams(
            audio_in_sample_rate=STT_INPUT_SAMPLE_RATE,
            audio_out_sample_rate=TTS_OUTPUT_SAMPLE_RATE,
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
        observers=[metrics_collector],
        enable_rtvi=False,
    )

    latency_observer = worker._user_bot_latency_observer

    attach_turn_logging(
        user_aggregator=context_aggregator.user(),
        assistant_aggregator=context_aggregator.assistant(),
        latency_observer=latency_observer,
        metrics_collector=metrics_collector,
        call_id=call_db_id,
        tenant_id=tenant_id,
        rag_state=rag_state,
    )

    return ConversationPipeline(
        worker=worker,
        user_aggregator=context_aggregator.user(),
        assistant_aggregator=context_aggregator.assistant(),
        latency_observer=latency_observer,
    )


def _build_hello_tone_pipeline(
    transport: FastAPIWebsocketTransport,
) -> PipelineWorker:

    pipeline = Pipeline([transport.input(), transport.output()])

    return PipelineWorker(
        pipeline,
        params=PipelineParams(
            audio_in_sample_rate=TWILIO_SAMPLE_RATE,
            audio_out_sample_rate=TTS_OUTPUT_SAMPLE_RATE,
        ),
        enable_rtvi=False,
    )


async def run_minimal_twilio_pipeline(
    websocket: WebSocket,
    settings: Settings,
) -> None:
    """Connect Twilio Media Streams to the Pipecat voice pipeline."""

    transport_type, call_data = await parse_telephony_websocket(websocket)

    if transport_type != "twilio":
        raise ValueError(f"Unsupported telephony transport: {transport_type}")

    stream_id = call_data["stream_id"]

    call_id = call_data.get("call_id")

    use_full_pipeline = bool(settings.deepgram_api_key and llm_key_present(settings))

    use_deepgram_only = bool(
        settings.deepgram_api_key and not llm_key_present(settings)
    )

    use_hello_tone = not settings.deepgram_api_key

    logger.info(
        "twilio_pipeline_starting",
        transport_type=transport_type,
        stream_id=stream_id,
        call_id=call_id,
        full_pipeline_enabled=use_full_pipeline,
        deepgram_only_enabled=use_deepgram_only,
        stt_sample_rate=(
            STT_INPUT_SAMPLE_RATE if not use_hello_tone else TWILIO_SAMPLE_RATE
        ),
        tts_sample_rate=TTS_OUTPUT_SAMPLE_RATE,
    )

    serializer = _build_twilio_serializer(
        stream_id=stream_id,
        call_id=call_id,
        settings=settings,
    )

    transport = _build_transport(websocket, serializer)

    conversation: ConversationPipeline | None = None

    hello_pcm: bytes | None = None

    if use_full_pipeline:
        ctx = await get_call_pipeline_context(call_id) if call_id else None

        if ctx is not None:
            # Stub/misconfigured providers fail here, before the call runs.
            ensure_live_providers(
                ProviderConfig(stt=ctx["stt"], tts=ctx["tts"], llm=ctx["llm"])
            )

        conversation = _build_conversation_pipeline(
            transport,
            settings,
            call_db_id=ctx["call_id"] if ctx else None,
            tenant_id=ctx["tenant_id"] if ctx else None,
            agent_id=ctx["agent_id"] if ctx else None,
            twilio_call_sid=call_id,
            voice_id=ctx["voice_id"] if ctx else None,
            system_prompt=ctx["system_prompt"] if ctx else None,
            tool_whitelist=list(ctx["tools"]) if ctx else None,
        )

        worker = conversation.worker

    elif use_deepgram_only:
        worker = _build_deepgram_only_pipeline(transport, settings)

    elif use_hello_tone:
        worker = _build_hello_tone_pipeline(transport)

        hello_pcm = generate_hello_audio_pcm()

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client) -> None:

        logger.info(
            "twilio_pipeline_connected",
            stream_id=stream_id,
            call_id=call_id,
            full_pipeline_enabled=use_full_pipeline,
        )

        if use_full_pipeline and conversation is not None:
            # Static greeting via TTS only — no LLM round-trip — so the caller
            # hears it within 800ms of connecting (ticket 2.16). It is already
            # seeded into the LLM context, so the conversation stays coherent.
            await conversation.worker.queue_frames([TTSSpeakFrame(GREETING_TEXT)])

        elif use_deepgram_only:
            await worker.queue_frames([TTSSpeakFrame(DEEPGRAM_CONNECT_GREETING)])

        elif hello_pcm is not None:
            await worker.queue_frames(
                [
                    OutputAudioRawFrame(
                        audio=hello_pcm,
                        sample_rate=TTS_OUTPUT_SAMPLE_RATE,
                        num_channels=1,
                    ),
                ]
            )

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client) -> None:

        logger.info(
            "twilio_pipeline_disconnected",
            stream_id=stream_id,
            call_id=call_id,
        )

        await worker.cancel()

    if call_id:
        agent_registry.register(call_id, worker)

    runner = WorkerRunner(handle_sigint=False, force_gc=True)

    try:
        await runner.add_workers(worker)

        await runner.run()

    finally:
        if call_id:
            agent_registry.unregister(call_id)

        logger.info(
            "twilio_pipeline_finished",
            stream_id=stream_id,
            call_id=call_id,
        )
