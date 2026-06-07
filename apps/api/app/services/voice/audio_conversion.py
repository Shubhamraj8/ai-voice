"""μ-law ↔ PCM conversion helpers using Pipecat's audio utilities (ticket 2.05)."""

from __future__ import annotations

from pipecat.audio.utils import create_file_resampler, pcm_to_ulaw, ulaw_to_pcm

from app.services.voice.audio_config import (
    STT_INPUT_SAMPLE_RATE,
    TTS_OUTPUT_SAMPLE_RATE,
    TWILIO_SAMPLE_RATE,
)


async def twilio_mulaw_to_stt_pcm(mulaw_bytes: bytes) -> bytes:
    """Convert Twilio μ-law 8 kHz payload to linear16 PCM for Deepgram STT."""
    resampler = create_file_resampler()
    return await ulaw_to_pcm(
        mulaw_bytes,
        TWILIO_SAMPLE_RATE,
        STT_INPUT_SAMPLE_RATE,
        resampler,
    )


async def tts_pcm_to_twilio_mulaw(pcm_bytes: bytes) -> bytes:
    """Convert Deepgram TTS linear16 PCM to Twilio μ-law 8 kHz payload."""
    resampler = create_file_resampler()
    return await pcm_to_ulaw(
        pcm_bytes,
        TTS_OUTPUT_SAMPLE_RATE,
        TWILIO_SAMPLE_RATE,
        resampler,
    )


async def pcm_to_twilio_mulaw_at_rate(pcm_bytes: bytes, *, sample_rate: int) -> bytes:
    """Convert arbitrary-rate linear16 PCM to Twilio μ-law 8 kHz."""
    resampler = create_file_resampler()
    return await pcm_to_ulaw(
        pcm_bytes,
        sample_rate,
        TWILIO_SAMPLE_RATE,
        resampler,
    )


async def twilio_mulaw_to_pcm_at_rate(mulaw_bytes: bytes, *, sample_rate: int) -> bytes:
    """Convert Twilio μ-law 8 kHz to linear16 PCM at the given rate."""
    resampler = create_file_resampler()
    return await ulaw_to_pcm(
        mulaw_bytes,
        TWILIO_SAMPLE_RATE,
        sample_rate,
        resampler,
    )
