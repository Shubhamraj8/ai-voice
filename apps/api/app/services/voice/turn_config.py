"""VAD, turn detection, and barge-in tuning for the Pipecat voice pipeline (2.10, 2.11).

Silero VAD detects local speech activity; Deepgram ``vad_events`` and
``endpointing`` provide server-side utterance boundaries. ``UserTurnProcessor``
combines both signals so the agent waits for end-of-speech before responding
and can interrupt TTS when the caller speaks again.

See ``app/services/voice/README.md`` for parameter descriptions.
"""

from __future__ import annotations

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.processors.audio.vad_processor import VADProcessor
from pipecat.turns.user_start import VADUserTurnStartStrategy
from pipecat.turns.user_stop import SpeechTimeoutUserTurnStopStrategy
from pipecat.turns.user_turn_processor import UserTurnProcessor
from pipecat.turns.user_turn_strategies import UserTurnStrategies

# Silero VAD — tuned for 8 kHz telephony resampled to 16 kHz STT input.
# Slightly relaxed thresholds help Indian-accent English on narrowband calls.
VAD_CONFIDENCE = 0.65
VAD_START_SECS = 0.25
VAD_STOP_SECS = 0.25
VAD_MIN_VOLUME = 0.55

# Policy floor after VAD reports silence — total turn-end within ~1 s of stop.
USER_TURN_END_TIMEOUT_SECS = 0.8

# Deepgram Listen API — matches provider layer (ticket 2.08).
DEEPGRAM_STT_MODEL = "nova-3"
DEEPGRAM_STT_LANGUAGE = "en"
DEEPGRAM_ENDPOINTING_MS = 300


def build_vad_params() -> VADParams:
    """Return Silero VAD parameters tuned for Indian English telephony."""

    return VADParams(
        confidence=VAD_CONFIDENCE,
        start_secs=VAD_START_SECS,
        stop_secs=VAD_STOP_SECS,
        min_volume=VAD_MIN_VOLUME,
    )


def build_vad_processor(*, sample_rate: int) -> VADProcessor:
    """Build a Silero VAD processor for the given pipeline sample rate."""

    return VADProcessor(
        vad_analyzer=SileroVADAnalyzer(
            sample_rate=sample_rate,
            params=build_vad_params(),
        ),
        speech_activity_period=0.2,
        audio_idle_timeout=1.0,
    )


def build_user_turn_strategies() -> UserTurnStrategies:
    """Turn start/stop strategies: VAD barge-in + 800 ms silence turn-end."""

    return UserTurnStrategies(
        start=[
            VADUserTurnStartStrategy(enable_interruptions=True),
        ],
        stop=[
            SpeechTimeoutUserTurnStopStrategy(
                user_speech_timeout=USER_TURN_END_TIMEOUT_SECS,
            ),
        ],
    )


def build_user_turn_processor() -> UserTurnProcessor:
    """Build turn processor with barge-in and end-of-speech detection."""

    return UserTurnProcessor(
        user_turn_strategies=build_user_turn_strategies(),
        user_turn_stop_timeout=5.0,
    )
