import audioop
import math
import struct

import pytest
from app.services.voice.audio_config import (
    STT_INPUT_SAMPLE_RATE,
    TTS_OUTPUT_SAMPLE_RATE,
    TWILIO_SAMPLE_RATE,
)
from app.services.voice.audio_conversion import (
    pcm_to_twilio_mulaw_at_rate,
    tts_pcm_to_twilio_mulaw,
    twilio_mulaw_to_pcm_at_rate,
    twilio_mulaw_to_stt_pcm,
)
from app.services.voice.pipeline import (
    HELLO_SAMPLE_RATE,
    generate_hello_audio_pcm,
)


def test_generate_hello_audio_pcm_produces_bytes():

    audio = generate_hello_audio_pcm()

    expected_samples = int(HELLO_SAMPLE_RATE * 1.2)

    assert len(audio) == expected_samples * 2

    assert audio != b"\x00" * len(audio)


def test_pipecat_imports_cleanly():

    import pipecat  # noqa: F401
    from pipecat.pipeline.pipeline import Pipeline  # noqa: F401
    from pipecat.serializers.twilio import TwilioFrameSerializer  # noqa: F401
    from pipecat.transports.websocket.fastapi import (  # noqa: F401
        FastAPIWebsocketTransport,
    )

    assert pipecat.__version__.startswith("1.")


def test_deepgram_imports_with_extra():

    from pipecat.services.deepgram.stt import DeepgramSTTService  # noqa: F401
    from pipecat.services.deepgram.tts import DeepgramTTSService  # noqa: F401


def test_twilio_media_route_registered():

    from app.main import app

    websocket_paths = [
        route.path
        for route in app.routes
        if getattr(route, "path", None) == "/webhooks/twilio/media"
    ]

    assert websocket_paths == ["/webhooks/twilio/media"]


def test_audio_config_sample_rates():

    assert TWILIO_SAMPLE_RATE == 8000

    assert STT_INPUT_SAMPLE_RATE == 16000

    assert TTS_OUTPUT_SAMPLE_RATE == 8000


def _generate_pcm_tone(*, sample_rate: int, duration_secs: float = 0.25) -> bytes:

    sample_count = int(sample_rate * duration_secs)

    samples = [
        int(8000 * math.sin(2 * math.pi * 440 * index / sample_rate))
        for index in range(sample_count)
    ]

    return struct.pack(f"<{len(samples)}h", *samples)


@pytest.mark.asyncio
async def test_mulaw_to_stt_pcm_resamples_to_16khz():

    pcm_8k = _generate_pcm_tone(sample_rate=TWILIO_SAMPLE_RATE)

    mulaw = audioop.lin2ulaw(pcm_8k, 2)

    pcm_16k = await twilio_mulaw_to_stt_pcm(mulaw)

    expected_samples = int(len(pcm_8k) / 2 * STT_INPUT_SAMPLE_RATE / TWILIO_SAMPLE_RATE)

    assert len(pcm_16k) == expected_samples * 2


@pytest.mark.asyncio
async def test_tts_pcm_to_mulaw_round_trip_at_8khz():

    pcm = _generate_pcm_tone(sample_rate=TTS_OUTPUT_SAMPLE_RATE)

    mulaw = await tts_pcm_to_twilio_mulaw(pcm)

    round_trip = await twilio_mulaw_to_pcm_at_rate(
        mulaw,
        sample_rate=TTS_OUTPUT_SAMPLE_RATE,
    )

    assert len(round_trip) == len(pcm)

    original = struct.unpack(f"<{len(pcm) // 2}h", pcm)

    restored = struct.unpack(f"<{len(round_trip) // 2}h", round_trip)

    max_delta = max(abs(a - b) for a, b in zip(original, restored, strict=True))

    assert max_delta < 3000


@pytest.mark.asyncio
async def test_mulaw_stt_round_trip_preserves_energy():

    pcm_16k = _generate_pcm_tone(sample_rate=STT_INPUT_SAMPLE_RATE)

    mulaw = await pcm_to_twilio_mulaw_at_rate(
        pcm_16k, sample_rate=STT_INPUT_SAMPLE_RATE
    )

    restored = await twilio_mulaw_to_stt_pcm(mulaw)

    assert len(restored) == len(pcm_16k)

    original_rms = audioop.rms(pcm_16k, 2)

    restored_rms = audioop.rms(restored, 2)

    assert restored_rms > original_rms * 0.5


def test_buffer_monitor_imports():

    from app.services.voice.buffer_monitor import AudioBufferUnderrunMonitor

    monitor = AudioBufferUnderrunMonitor()

    assert monitor._underrun_count == 0
