"""Provider implementations (tickets 2.06, 2.07).

Phase map
---------
Phase 2  (LIVE)     : DeepgramSTT  → real impl in deepgram_stt.py
                    : Nova-3 streaming STT (ticket 2.08)
Phase 2  (LIVE)     : DeepgramTTS  → real impl in deepgram_tts.py
                    : Aura-1 streaming TTS (ticket 2.07)
Phase 2  (LIVE)     : DeepSeekNativeLLM → real impl in deepseek_llm.py
                    : V4 Flash via native API (ticket 2.09)
Phase 3  (next)     : SarvamSTT, SarvamTTS                          — India Hindi market
Phase 3  (next)     : DeepgramSTTEnterprise, DeepgramTTSEnterprise   — US HIPAA BAA tier
Phase 3  (next)     : TogetherDeepSeekLLM                            — US HIPAA LLM tier
Phase 4  (future)   : OpenAIRealtimeSTT, OpenAITTS, ElevenLabsTTS    — global expansion
Phase 4  (future)   : OpenAIGPT5MiniLLM                              — latency fallback
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from app.providers.base import LLMResponse, Message, Transcript

# Re-export live provider implementations (tickets 2.07–2.09)
from app.providers.deepgram_stt import DeepgramSTT  # noqa: F401  (re-export)
from app.providers.deepgram_tts import DeepgramTTS  # noqa: F401  (re-export)
from app.providers.deepseek_llm import DeepSeekNativeLLM  # noqa: F401  (re-export)

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _not_implemented(cls_name: str, phase: str) -> NotImplementedError:
    return NotImplementedError(
        f"{cls_name} is not yet implemented. "
        f"It will be wired up in {phase}. "
        "Check docs/tickets.md for the relevant ticket."
    )


# ---------------------------------------------------------------------------
# Phase 2 — India English (LIVE stubs — real implementations in Phase 2 tickets)
# ---------------------------------------------------------------------------


# DeepgramSTT is a LIVE implementation imported above from deepgram_stt.py.
# DeepgramTTS is a LIVE implementation imported above from deepgram_tts.py.
# The class is re-exported so that existing code importing from stubs.py continues
# to work unchanged.  See app/providers/deepgram_tts.py for full source.


# DeepSeekNativeLLM is a LIVE implementation imported above from deepseek_llm.py.


# ---------------------------------------------------------------------------
# Phase 3 — India Hindi market (Sarvam AI)
# ---------------------------------------------------------------------------


class SarvamSTT:
    """Sarvam AI STT — India Hindi / Hinglish market.

    Real implementation: Phase 3 (India Hindi market sprint).
    Blocked on: Sarvam AI API access and BAA review.
    """

    async def connect(self, language: str) -> None:
        raise _not_implemented(
            "SarvamSTT",
            "Phase 3 (India Hindi market — see ticket 3.xx)",
        )

    async def stream(
        self,
        audio_chunks: AsyncIterator[bytes],
    ) -> AsyncIterator[Transcript]:
        raise _not_implemented(
            "SarvamSTT",
            "Phase 3 (India Hindi market — see ticket 3.xx)",
        )
        yield

    async def close(self) -> None:
        raise _not_implemented(
            "SarvamSTT",
            "Phase 3 (India Hindi market — see ticket 3.xx)",
        )


class SarvamTTS:
    """Sarvam AI TTS — India Hindi / Hinglish market.

    Real implementation: Phase 3 (India Hindi market sprint).
    Blocked on: Sarvam AI API access.
    """

    async def synthesize(
        self,
        text: str,
        voice_id: str,
        language: str,
    ) -> AsyncIterator[bytes]:
        raise _not_implemented(
            "SarvamTTS",
            "Phase 3 (India Hindi market — see ticket 3.xx)",
        )
        yield


# ---------------------------------------------------------------------------
# Phase 3 — US HIPAA tier (Deepgram BAA + Together AI)
# ---------------------------------------------------------------------------


class DeepgramSTTEnterprise:
    """Deepgram STT under a signed BAA — US HIPAA-eligible tier.

    Real implementation: Phase 3 (US HIPAA tier).
    Blocked on: Deepgram Enterprise contract + BAA signature.
    """

    async def connect(self, language: str) -> None:
        raise _not_implemented(
            "DeepgramSTTEnterprise",
            "Phase 3 (US HIPAA tier — Deepgram BAA required)",
        )

    async def stream(
        self,
        audio_chunks: AsyncIterator[bytes],
    ) -> AsyncIterator[Transcript]:
        raise _not_implemented(
            "DeepgramSTTEnterprise",
            "Phase 3 (US HIPAA tier — Deepgram BAA required)",
        )
        yield

    async def close(self) -> None:
        raise _not_implemented(
            "DeepgramSTTEnterprise",
            "Phase 3 (US HIPAA tier — Deepgram BAA required)",
        )


class DeepgramTTSEnterprise:
    """Deepgram TTS under a signed BAA — US HIPAA-eligible tier.

    Real implementation: Phase 3 (US HIPAA tier).
    Blocked on: Deepgram Enterprise contract + BAA signature.
    """

    async def synthesize(
        self,
        text: str,
        voice_id: str,
        language: str,
    ) -> AsyncIterator[bytes]:
        raise _not_implemented(
            "DeepgramTTSEnterprise",
            "Phase 3 (US HIPAA tier — Deepgram BAA required)",
        )
        yield


class TogetherDeepSeekLLM:
    """DeepSeek via Together AI — US HIPAA-eligible LLM tier.

    Real implementation: Phase 3 (US HIPAA tier).
    Blocked on: Together AI HIPAA BAA + US HIPAA Twilio account.
    """

    async def chat(
        self,
        messages: list[Message],
        tools: list[dict],
        max_tokens: int = 200,
    ) -> LLMResponse:
        raise _not_implemented(
            "TogetherDeepSeekLLM",
            "Phase 3 (US HIPAA tier — Together AI BAA required)",
        )


# ---------------------------------------------------------------------------
# Phase 4 — Global / fallback providers
# ---------------------------------------------------------------------------


class OpenAIRealtimeSTT:
    """OpenAI Realtime API STT — global English fallback / low-latency tier."""

    async def connect(self, language: str) -> None:
        raise _not_implemented(
            "OpenAIRealtimeSTT",
            "Phase 4 (global English / latency fallback)",
        )

    async def stream(
        self,
        audio_chunks: AsyncIterator[bytes],
    ) -> AsyncIterator[Transcript]:
        raise _not_implemented(
            "OpenAIRealtimeSTT",
            "Phase 4 (global English / latency fallback)",
        )
        yield

    async def close(self) -> None:
        raise _not_implemented(
            "OpenAIRealtimeSTT",
            "Phase 4 (global English / latency fallback)",
        )


class OpenAITTS:
    """OpenAI TTS — global English fallback."""

    async def synthesize(
        self,
        text: str,
        voice_id: str,
        language: str,
    ) -> AsyncIterator[bytes]:
        raise _not_implemented(
            "OpenAITTS",
            "Phase 4 (global English / latency fallback)",
        )
        yield


class ElevenLabsTTS:
    """ElevenLabs TTS — premium voice quality option."""

    async def synthesize(
        self,
        text: str,
        voice_id: str,
        language: str,
    ) -> AsyncIterator[bytes]:
        raise _not_implemented(
            "ElevenLabsTTS",
            "Phase 4 (global English / latency fallback)",
        )
        yield


class OpenAIGPT5MiniLLM:
    """OpenAI GPT-5 Mini — latency fallback LLM."""

    async def chat(
        self,
        messages: list[Message],
        tools: list[dict],
        max_tokens: int = 200,
    ) -> LLMResponse:
        raise _not_implemented(
            "OpenAIGPT5MiniLLM",
            "Phase 4 (global English / latency fallback)",
        )


# ---------------------------------------------------------------------------
# Type aliases (for isinstance / Protocol checks in tests)
# ---------------------------------------------------------------------------

AnySTTProvider = DeepgramSTT | DeepgramSTTEnterprise | SarvamSTT | OpenAIRealtimeSTT

AnyTTSProvider = (
    DeepgramTTS | DeepgramTTSEnterprise | SarvamTTS | OpenAITTS | ElevenLabsTTS
)

AnyLLMProvider = DeepSeekNativeLLM | TogetherDeepSeekLLM | OpenAIGPT5MiniLLM
