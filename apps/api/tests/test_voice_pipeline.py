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
from app.services.voice.conversation_config import (
    MAX_CONVERSATION_TURNS,
    MAX_LLM_OUTPUT_TOKENS,
    SYSTEM_PROMPT,
    build_llm_context,
    trim_conversation_history,
)
from app.services.voice.pipeline import (
    HELLO_SAMPLE_RATE,
    _build_deepgram_stt_settings,
    _normalize_deepseek_base_url,
    generate_hello_audio_pcm,
)
from app.services.voice.turn_config import (
    DEEPGRAM_ENDPOINTING_MS,
    DEEPGRAM_STT_MODEL,
    USER_TURN_END_TIMEOUT_SECS,
    VAD_CONFIDENCE,
    VAD_STOP_SECS,
    build_user_turn_processor,
    build_user_turn_strategies,
    build_vad_params,
    build_vad_processor,
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


def test_vad_turn_config_defaults():

    params = build_vad_params()

    assert params.confidence == VAD_CONFIDENCE

    assert params.stop_secs == VAD_STOP_SECS

    assert USER_TURN_END_TIMEOUT_SECS == 0.8


def test_vad_processor_uses_silero_at_stt_sample_rate():

    from pipecat.audio.vad.silero import SileroVADAnalyzer
    from pipecat.processors.audio.vad_processor import VADProcessor

    processor = build_vad_processor(sample_rate=STT_INPUT_SAMPLE_RATE)

    assert isinstance(processor, VADProcessor)

    assert isinstance(processor._vad_controller._vad_analyzer, SileroVADAnalyzer)

    analyzer = processor._vad_controller._vad_analyzer

    assert analyzer._init_sample_rate == STT_INPUT_SAMPLE_RATE


def test_user_turn_strategies_enable_barge_in_and_speech_timeout():

    from pipecat.turns.user_start import VADUserTurnStartStrategy
    from pipecat.turns.user_stop import SpeechTimeoutUserTurnStopStrategy

    strategies = build_user_turn_strategies()

    assert len(strategies.start) == 1

    assert isinstance(strategies.start[0], VADUserTurnStartStrategy)

    assert strategies.start[0]._enable_interruptions is True

    assert len(strategies.stop) == 1

    assert isinstance(strategies.stop[0], SpeechTimeoutUserTurnStopStrategy)

    assert strategies.stop[0]._user_speech_timeout == USER_TURN_END_TIMEOUT_SECS


def test_user_turn_processor_wires_strategies():

    processor = build_user_turn_processor()

    stop_strategy = processor._user_turn_controller._user_turn_strategies.stop[0]

    assert stop_strategy._user_speech_timeout == 0.8


def test_deepgram_stt_settings_for_turn_detection():

    from pipecat.services.settings import is_given

    settings = _build_deepgram_stt_settings()

    assert is_given(settings.model)

    assert settings.model == DEEPGRAM_STT_MODEL

    assert is_given(settings.smart_format)

    assert settings.smart_format is True

    assert is_given(settings.endpointing)

    assert settings.endpointing == DEEPGRAM_ENDPOINTING_MS

    assert settings.extra["vad_events"] is True


def test_vad_and_turn_imports():

    from pipecat.processors.audio.vad_processor import VADProcessor  # noqa: F401
    from pipecat.turns.user_turn_processor import UserTurnProcessor  # noqa: F401


def test_conversation_config_defaults():

    context = build_llm_context()

    assert context.messages[0]["role"] == "system"

    assert SYSTEM_PROMPT in context.messages[0]["content"]

    assert MAX_CONVERSATION_TURNS == 10

    assert MAX_LLM_OUTPUT_TOKENS == 200


def test_trim_conversation_history_keeps_system_and_last_ten_turns():

    context = build_llm_context()

    for index in range(15):
        context.add_message({"role": "user", "content": f"user-{index}"})
        context.add_message({"role": "assistant", "content": f"assistant-{index}"})

    trim_conversation_history(context, max_turns=10)

    assert context.messages[0]["role"] == "system"

    assert len(context.messages) == 1 + (10 * 2)

    assert context.messages[1]["content"] == "user-5"

    assert context.messages[-1]["content"] == "assistant-14"


def test_normalize_deepseek_base_url_adds_v1_suffix():

    assert (
        _normalize_deepseek_base_url("https://api.deepseek.com")
        == "https://api.deepseek.com/v1"
    )

    assert (
        _normalize_deepseek_base_url("https://api.deepseek.com/v1")
        == "https://api.deepseek.com/v1"
    )


def test_full_pipeline_llm_imports():

    from pipecat.processors.aggregators.llm_response_universal import (  # noqa: F401
        LLMContextAggregatorPair,
    )
    from pipecat.services.deepseek.llm import DeepSeekLLMService  # noqa: F401
    from pipecat.turns.user_turn_strategies import (
        ExternalUserTurnStrategies,  # noqa: F401
    )


def test_build_deepseek_llm_service_uses_app_settings(monkeypatch):

    from app.config import Settings
    from app.services.voice.pipeline import _build_deepseek_llm_service

    settings = Settings(
        database_url="postgresql://example",
        supabase_url="https://example.supabase.co",
        supabase_service_role_key="key",
        deepseek_api_key="sk-test",
        deepseek_base_url="https://api.deepseek.com",
        deepseek_model="deepseek-v4-flash",
    )

    llm = _build_deepseek_llm_service(settings)

    assert llm._settings.model == "deepseek-v4-flash"

    assert llm._settings.max_tokens == MAX_LLM_OUTPUT_TOKENS
