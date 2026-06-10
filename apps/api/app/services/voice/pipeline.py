"""Pipecat voice pipeline for Twilio Media Streams (tickets 2.04–2.11)."""

from __future__ import annotations

import math
import struct
from typing import TYPE_CHECKING

import structlog
from fastapi import WebSocket
from pipecat.frames.frames import OutputAudioRawFrame, TTSSpeakFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineParams, PipelineWorker
from pipecat.runner.utils import parse_telephony_websocket
from pipecat.serializers.twilio import TwilioFrameSerializer
from pipecat.transports.websocket.fastapi import (
    FastAPIWebsocketParams,
    FastAPIWebsocketTransport,
)
from pipecat.workers.runner import WorkerRunner

from app.services.voice.audio_config import (
    STT_INPUT_SAMPLE_RATE,
    TTS_OUTPUT_SAMPLE_RATE,
    TWILIO_SAMPLE_RATE,
)
from app.services.voice.buffer_monitor import AudioBufferUnderrunMonitor
from app.services.voice.turn_config import (
    DEEPGRAM_ENDPOINTING_MS,
    DEEPGRAM_STT_LANGUAGE,
    DEEPGRAM_STT_MODEL,
    build_user_turn_processor,
    build_vad_processor,
)

if TYPE_CHECKING:
    from app.config import Settings


logger = structlog.get_logger(__name__)


HELLO_SAMPLE_RATE = TTS_OUTPUT_SAMPLE_RATE

HELLO_DURATION_SECS = 1.2

HELLO_FREQUENCY_HZ = 523

DEEPGRAM_CONNECT_GREETING = "Audio pipeline connected."


def generate_hello_audio_pcm(
    *,
    sample_rate: int = HELLO_SAMPLE_RATE,
    duration_secs: float = HELLO_DURATION_SECS,
    frequency_hz: int = HELLO_FREQUENCY_HZ,
) -> bytes:
    """Generate a short PCM16 tone callers hear when Deepgram is not configured."""

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


def _build_deepgram_pipeline(
    transport: FastAPIWebsocketTransport,
    settings: Settings,
) -> tuple[Pipeline, PipelineWorker]:

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

    worker = PipelineWorker(
        pipeline,
        params=PipelineParams(
            audio_in_sample_rate=STT_INPUT_SAMPLE_RATE,
            audio_out_sample_rate=TTS_OUTPUT_SAMPLE_RATE,
        ),
    )

    return pipeline, worker


def _build_hello_tone_pipeline(
    transport: FastAPIWebsocketTransport,
) -> tuple[Pipeline, PipelineWorker]:

    pipeline = Pipeline([transport.input(), transport.output()])

    worker = PipelineWorker(
        pipeline,
        params=PipelineParams(
            audio_in_sample_rate=TWILIO_SAMPLE_RATE,
            audio_out_sample_rate=TTS_OUTPUT_SAMPLE_RATE,
        ),
    )

    return pipeline, worker


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

    use_deepgram = bool(settings.deepgram_api_key)

    logger.info(
        "twilio_pipeline_starting",
        transport_type=transport_type,
        stream_id=stream_id,
        call_id=call_id,
        deepgram_enabled=use_deepgram,
        stt_sample_rate=STT_INPUT_SAMPLE_RATE if use_deepgram else TWILIO_SAMPLE_RATE,
        tts_sample_rate=TTS_OUTPUT_SAMPLE_RATE,
    )

    serializer = _build_twilio_serializer(
        stream_id=stream_id,
        call_id=call_id,
        settings=settings,
    )

    transport = _build_transport(websocket, serializer)

    if use_deepgram:
        _, worker = _build_deepgram_pipeline(transport, settings)

        hello_pcm = None

    else:
        _, worker = _build_hello_tone_pipeline(transport)

        hello_pcm = generate_hello_audio_pcm()

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client) -> None:

        logger.info(
            "twilio_pipeline_connected",
            stream_id=stream_id,
            call_id=call_id,
            deepgram_enabled=use_deepgram,
        )

        if use_deepgram:
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

    runner = WorkerRunner(handle_sigint=False, force_gc=True)

    try:
        await runner.add_workers(worker)

        await runner.run()

    finally:
        logger.info(
            "twilio_pipeline_finished",
            stream_id=stream_id,
            call_id=call_id,
        )
