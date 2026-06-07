"""Deepgram Aura-1 TTS provider — ticket 2.07.

Implements the TTSProvider protocol via the Deepgram Speak REST streaming API
(deepgram-sdk v7+).  Audio is streamed as 16-bit linear PCM at 8 kHz —
directly compatible with Twilio <Stream> media without transcoding.

Key features
------------
- Streaming via ``AsyncDeepgramClient.speak.v1.audio.generate()``
- Encoding: linear16, 8000 Hz (direct Twilio compatibility)
- Default voice: aura-asteria-en (Indian-English-friendly)
- Per-call ``tts_chars`` metric emitted via structlog for cost tracking
  ($0.015 / 1 000 chars on Aura-1)
- Retry with exponential back-off (up to 3 attempts) on transient errors
- Time-to-first-byte (TTFB) and total synthesis time logged on every call

SDK version
-----------
deepgram-sdk >= 7.0.0 — uses the new REST Speak streaming API
(``client.speak.v1.audio.generate`` → ``AsyncIterator[bytes]``)
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator

import structlog
from deepgram import AsyncDeepgramClient

from app.config import get_settings

log = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Default Deepgram Aura-1 voice — Indian-English-friendly.
_DEFAULT_VOICE = "aura-asteria-en"

#: PCM encoding for Twilio <Stream> compatibility.
_ENCODING = "linear16"

#: Sample rate must match Twilio's media stream (8 kHz).
_SAMPLE_RATE = 8000

#: Maximum retries on transient API / network errors.
_MAX_RETRIES = 3

#: Initial back-off delay seconds (doubles each retry).
_BACKOFF_BASE = 0.5

# ---------------------------------------------------------------------------
# Voice catalogue (Deepgram Aura-1 voices — Phase 3 agent-edit form)
# ---------------------------------------------------------------------------
# Documented in /services/voice/providers/README.md
VOICE_CATALOGUE: list[str] = [
    "aura-asteria-en",  # 🇮🇳 Indian-English-friendly (default)
    "aura-luna-en",  # US female — calm
    "aura-stella-en",  # US female — warm
    "aura-athena-en",  # UK female — authoritative
    "aura-hera-en",  # US female — professional
    "aura-orion-en",  # US male — deep
    "aura-arcas-en",  # US male — casual
    "aura-perseus-en",  # US male — crisp
    "aura-angus-en",  # Irish male — friendly
    "aura-orpheus-en",  # US male — clear
    "aura-helios-en",  # UK male — warm
    "aura-zeus-en",  # US male — authoritative
]


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------


class DeepgramTTS:
    """Deepgram Aura-1 TTS via the Speak streaming REST API (SDK v7).

    Satisfies the TTSProvider protocol (app/providers/base.py).

    Usage::

        tts = DeepgramTTS()
        async for chunk in tts.synthesize("Hello!", "aura-asteria-en", "en"):
            # chunk: raw PCM bytes — linear16, 8 kHz, mono
            await websocket.send_bytes(chunk)
    """

    # ------------------------------------------------------------------
    # TTSProvider protocol method
    # ------------------------------------------------------------------

    async def synthesize(
        self,
        text: str,
        voice_id: str = _DEFAULT_VOICE,
        language: str = "en",
    ) -> AsyncIterator[bytes]:
        """Synthesize *text* via Deepgram Aura-1 and stream PCM audio chunks.

        Args:
            text:     The utterance to synthesize.  Keep ≤ 150 chars (~25 words)
                      for the concise-reply budget.
            voice_id: Deepgram model name (e.g. ``"aura-asteria-en"``).  Defaults
                      to ``aura-asteria-en`` if unknown or empty.
            language: BCP-47 language tag — informational only (Aura-1 voices
                      are single-language).

        Yields:
            Raw PCM audio bytes (linear16, 8 kHz, mono).

        Raises:
            RuntimeError: After all retry attempts are exhausted.
        """
        if not voice_id:
            voice_id = _DEFAULT_VOICE
        if voice_id not in VOICE_CATALOGUE:
            log.warning(
                "deepgram_tts.unknown_voice",
                voice_id=voice_id,
                fallback=_DEFAULT_VOICE,
            )
            voice_id = _DEFAULT_VOICE

        char_count = len(text)

        attempt = 0
        last_error: Exception | None = None

        while attempt < _MAX_RETRIES:
            attempt += 1
            try:
                async for chunk in self._synthesize_once(
                    text=text,
                    voice_id=voice_id,
                    char_count=char_count,
                    attempt=attempt,
                ):
                    yield chunk
                return  # success
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt < _MAX_RETRIES:
                    delay = _BACKOFF_BASE * (2 ** (attempt - 1))
                    log.warning(
                        "deepgram_tts.retry",
                        attempt=attempt,
                        delay_s=delay,
                        error=str(exc),
                    )
                    await asyncio.sleep(delay)
                else:
                    log.error(
                        "deepgram_tts.failed",
                        attempts=attempt,
                        error=str(exc),
                        tts_chars=char_count,
                    )

        raise RuntimeError(
            f"DeepgramTTS: all {_MAX_RETRIES} synthesis attempts failed. "
            f"Last error: {last_error}"
        ) from last_error

    # ------------------------------------------------------------------
    # Internal helper
    # ------------------------------------------------------------------

    async def _synthesize_once(
        self,
        text: str,
        voice_id: str,
        char_count: int,
        attempt: int,
    ) -> AsyncIterator[bytes]:
        """Single synthesis attempt via Deepgram Speak streaming REST API.

        Yields PCM chunks as they arrive.  Logs TTFB and total duration.
        """
        settings = get_settings()
        api_key = settings.deepgram_api_key
        if not api_key:
            raise RuntimeError(
                "DEEPGRAM_API_KEY is not set — cannot synthesize audio. "
                "Set it in .env or Render environment variables."
            )

        client = AsyncDeepgramClient(api_key=api_key)

        t_start = time.monotonic()
        t_first_byte: float | None = None

        try:
            stream: AsyncIterator[bytes] = await client.speak.v1.audio.generate(
                text=text,
                model=voice_id,  # type: ignore[arg-type]
                encoding=_ENCODING,  # type: ignore[arg-type]
                sample_rate=float(_SAMPLE_RATE),
            )

            async for chunk in stream:
                if chunk:  # skip empty keepalive frames
                    if t_first_byte is None:
                        t_first_byte = time.monotonic()
                    yield chunk

        finally:
            t_end = time.monotonic()
            ttfb_ms = round((t_first_byte - t_start) * 1000) if t_first_byte else None
            total_ms = round((t_end - t_start) * 1000)

            log.info(
                "deepgram_tts.synthesized",
                voice_id=voice_id,
                tts_chars=char_count,
                ttfb_ms=ttfb_ms,
                total_ms=total_ms,
                attempt=attempt,
                cost_usd=round(char_count * 0.015 / 1000, 6),
            )
