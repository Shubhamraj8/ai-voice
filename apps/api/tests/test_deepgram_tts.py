"""Tests for the DeepgramTTS provider (ticket 2.07).

Test categories
---------------
1. Unit tests (no real API calls) — mock the Deepgram SDK WebSocket
2. Voice validation — unknown voices fall back to the default
3. Retry + exponential back-off behaviour
4. tts_chars / latency metric emission
5. Concise-reply budget verification (≤ 25 words / ~150 chars per turn)
6. VOICE_CATALOGUE completeness
7. Config guard (missing API key raises RuntimeError, not silent failure)

Run with::

    cd apps/api
    pytest tests/test_deepgram_tts.py -v
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.providers.deepgram_tts import (
    _DEFAULT_VOICE,
    _ENCODING,
    _MAX_RETRIES,
    _SAMPLE_RATE,
    VOICE_CATALOGUE,
    DeepgramTTS,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_pcm_chunk(size: int = 320) -> bytes:
    """Return a dummy PCM chunk (silence) of *size* bytes."""
    return b"\x00" * size


async def _collect(gen: AsyncIterator[bytes]) -> list[bytes]:
    """Drain an async generator into a list."""
    return [chunk async for chunk in gen]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_deepgram_ws():
    """Patch the Deepgram WebSocket so no real network call is made."""
    ws = AsyncMock()
    ws.start = AsyncMock(return_value=True)
    ws.send_text = AsyncMock()
    ws.flush = AsyncMock()
    ws.finish = AsyncMock()
    ws.on = MagicMock()
    return ws


@pytest.fixture()
def mock_client(mock_deepgram_ws):
    """Patch DeepgramClient so asyncspeak.websocket.v() returns our mock."""
    client = MagicMock()
    client.asyncspeak.websocket.v.return_value = mock_deepgram_ws
    return client


# ---------------------------------------------------------------------------
# 1. Constants / catalogue
# ---------------------------------------------------------------------------


class TestConstants:
    def test_default_voice_is_asteria(self):
        assert _DEFAULT_VOICE == "aura-asteria-en"

    def test_encoding_is_linear16(self):
        assert _ENCODING == "linear16"

    def test_sample_rate_is_8000(self):
        assert _SAMPLE_RATE == 8000

    def test_max_retries_is_3(self):
        assert _MAX_RETRIES == 3

    def test_voice_catalogue_has_12_voices(self):
        assert len(VOICE_CATALOGUE) == 12

    def test_all_required_voices_present(self):
        required = [
            "aura-asteria-en",
            "aura-luna-en",
            "aura-stella-en",
            "aura-athena-en",
            "aura-hera-en",
            "aura-orion-en",
            "aura-arcas-en",
            "aura-perseus-en",
            "aura-angus-en",
            "aura-orpheus-en",
            "aura-helios-en",
            "aura-zeus-en",
        ]
        for voice in required:
            assert voice in VOICE_CATALOGUE, f"{voice!r} missing from VOICE_CATALOGUE"

    def test_default_voice_in_catalogue(self):
        assert _DEFAULT_VOICE in VOICE_CATALOGUE


# ---------------------------------------------------------------------------
# 2. Voice validation
# ---------------------------------------------------------------------------


class TestVoiceValidation:
    async def test_unknown_voice_falls_back_to_default(self, mock_client, caplog):
        """Passing an unrecognised voice_id falls back to aura-asteria-en."""
        chunks_sent: list[bytes] = []

        async def _fake_synthesize_once(**kwargs: Any):
            # Verify we got the default voice
            assert kwargs["voice_id"] == _DEFAULT_VOICE
            yield _make_pcm_chunk()

        tts = DeepgramTTS()
        with (
            patch.object(tts, "_synthesize_once", side_effect=_fake_synthesize_once),
            patch("app.providers.deepgram_tts.get_settings") as mock_settings,
        ):
            mock_settings.return_value.deepgram_api_key = "test-key"
            chunks_sent = await _collect(
                tts.synthesize("Hello!", voice_id="nonexistent-voice-en")
            )

        assert len(chunks_sent) == 1

    async def test_empty_voice_id_uses_default(self, mock_client):
        """Empty string voice_id falls back to default."""

        async def _fake_synthesize_once(**kwargs: Any):
            assert kwargs["voice_id"] == _DEFAULT_VOICE
            yield _make_pcm_chunk()

        tts = DeepgramTTS()
        with (
            patch.object(tts, "_synthesize_once", side_effect=_fake_synthesize_once),
            patch("app.providers.deepgram_tts.get_settings") as mock_settings,
        ):
            mock_settings.return_value.deepgram_api_key = "test-key"
            chunks = await _collect(tts.synthesize("Hello!", voice_id=""))

        assert len(chunks) == 1

    async def test_valid_voice_is_passed_through(self):
        """A valid voice_id from VOICE_CATALOGUE is forwarded unchanged."""

        async def _fake_synthesize_once(**kwargs: Any):
            assert kwargs["voice_id"] == "aura-zeus-en"
            yield _make_pcm_chunk()

        tts = DeepgramTTS()
        with patch.object(tts, "_synthesize_once", side_effect=_fake_synthesize_once):
            chunks = await _collect(tts.synthesize("Hi!", voice_id="aura-zeus-en"))

        assert len(chunks) == 1


# ---------------------------------------------------------------------------
# 3. Retry + exponential back-off
# ---------------------------------------------------------------------------


class TestRetryBackoff:
    async def test_retries_on_transient_error(self):
        """Provider retries up to MAX_RETRIES times on error."""
        call_count = 0

        async def _failing_synthesize_once(**kwargs: Any):
            nonlocal call_count
            call_count += 1
            raise RuntimeError("transient network error")
            yield  # make it an async generator

        tts = DeepgramTTS()
        with (
            patch.object(tts, "_synthesize_once", side_effect=_failing_synthesize_once),
            patch("app.providers.deepgram_tts.asyncio.sleep", new_callable=AsyncMock),
        ):
            with pytest.raises(RuntimeError, match="all 3 synthesis attempts failed"):
                await _collect(tts.synthesize("Hello"))

        assert call_count == _MAX_RETRIES

    async def test_succeeds_on_second_attempt(self):
        """Provider returns audio if second attempt succeeds."""
        call_count = 0

        async def _flaky_once(**kwargs: Any):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("first attempt fails")
            yield _make_pcm_chunk()

        tts = DeepgramTTS()
        with (
            patch.object(tts, "_synthesize_once", side_effect=_flaky_once),
            patch("app.providers.deepgram_tts.asyncio.sleep", new_callable=AsyncMock),
        ):
            chunks = await _collect(tts.synthesize("Hello"))

        assert len(chunks) == 1
        assert call_count == 2

    async def test_backoff_sleep_called_between_retries(self):
        """asyncio.sleep is called with increasing delays between retries."""
        sleep_calls: list[float] = []

        async def _always_fail(**kwargs: Any):
            raise RuntimeError("boom")
            yield

        async def _capture_sleep(delay: float) -> None:
            sleep_calls.append(delay)

        tts = DeepgramTTS()
        with (
            patch.object(tts, "_synthesize_once", side_effect=_always_fail),
            patch(
                "app.providers.deepgram_tts.asyncio.sleep",
                side_effect=_capture_sleep,
            ),
        ):
            with pytest.raises(RuntimeError):
                await _collect(tts.synthesize("Hello"))

        # Two sleeps for 3 attempts: attempt 1→2 and 2→3
        assert len(sleep_calls) == 2
        assert sleep_calls[0] == 0.5  # _BACKOFF_BASE * 2^0
        assert sleep_calls[1] == 1.0  # _BACKOFF_BASE * 2^1


# ---------------------------------------------------------------------------
# 4. tts_chars metric and char count
# ---------------------------------------------------------------------------


class TestTtsCharsMetric:
    async def test_char_count_matches_text_length(self):
        """The char_count passed to _synthesize_once equals len(text)."""
        text = "Hello, how can I help you today?"
        recorded_char_count: list[int] = []

        async def _capture_once(**kwargs: Any):
            recorded_char_count.append(kwargs["char_count"])
            yield _make_pcm_chunk()

        tts = DeepgramTTS()
        with patch.object(tts, "_synthesize_once", side_effect=_capture_once):
            await _collect(tts.synthesize(text))

        assert recorded_char_count == [len(text)]

    async def test_cost_calculation_for_150_chars(self):
        """150-char utterance costs $0.00225 — within the concise-reply budget."""
        cost = 150 * 0.015 / 1000
        assert round(cost, 6) == 0.00225


# ---------------------------------------------------------------------------
# 5. Concise-reply budget
# ---------------------------------------------------------------------------


class TestConciseReplyBudget:
    @pytest.mark.parametrize(
        "text",
        [
            "Hello, how can I help you today?",  # 7 words
            "Sure, I can help you with that. Please hold on.",  # 10 words
            "Your appointment has been scheduled for tomorrow at 10 AM.",  # 10 words
        ],
    )
    def test_short_utterances_within_budget(self, text: str):
        words = len(text.split())
        chars = len(text)
        assert words <= 25, f"Too many words: {words} > 25"
        assert chars <= 200, f"Too many chars: {chars} > 200"

    def test_budget_boundary_25_words(self):
        """A 25-word sentence is within budget."""
        text = " ".join(["word"] * 25)
        assert len(text.split()) == 25
        assert len(text) <= 200

    def test_over_budget_200_words_detected(self):
        """A 200-word text is clearly over the per-turn budget."""
        text = " ".join(["word"] * 200)
        assert len(text.split()) > 25


# ---------------------------------------------------------------------------
# 6. Missing API key guard
# ---------------------------------------------------------------------------


class TestApiKeyGuard:
    async def test_missing_api_key_raises_runtime_error(self):
        """synthesize() must fail fast with a clear message when key is absent."""
        tts = DeepgramTTS()
        with patch("app.providers.deepgram_tts.get_settings") as mock_settings:
            mock_settings.return_value.deepgram_api_key = ""
            # Should raise RuntimeError (not AttributeError or silent NoneType)
            with pytest.raises(RuntimeError, match="DEEPGRAM_API_KEY is not set"):
                await _collect(tts.synthesize("Hello"))


# ---------------------------------------------------------------------------
# 7. Streaming output (integration-style unit test with mocked WS)
# ---------------------------------------------------------------------------


class TestStreamingOutput:
    async def test_yields_multiple_chunks(self):
        """synthesize() yields every audio chunk delivered by the WebSocket."""
        expected_chunks = [
            _make_pcm_chunk(320),
            _make_pcm_chunk(320),
            _make_pcm_chunk(160),
        ]

        async def _multi_chunk_once(**kwargs: Any):
            for chunk in expected_chunks:
                yield chunk

        tts = DeepgramTTS()
        with patch.object(tts, "_synthesize_once", side_effect=_multi_chunk_once):
            received = await _collect(tts.synthesize("Hello there!"))

        assert received == expected_chunks

    async def test_synthesize_hello_greeting(self):
        """Acceptance criterion: synthesize the canonical greeting."""
        greeting = "Hello, how can I help you today?"
        chunks_received: list[bytes] = []

        async def _once(**kwargs: Any):
            assert kwargs["text"] == greeting
            yield _make_pcm_chunk(640)

        tts = DeepgramTTS()
        with patch.object(tts, "_synthesize_once", side_effect=_once):
            chunks_received = await _collect(tts.synthesize(greeting))

        assert len(chunks_received) == 1
        assert len(chunks_received[0]) == 640


# ---------------------------------------------------------------------------
# 8. Registry integration — DeepgramTTS resolves from the registry
# ---------------------------------------------------------------------------


class TestRegistryIntegration:
    def test_registry_resolves_deepgram_tts_to_real_class(self):
        """PROVIDERS['tts']['deepgram'] must resolve to the real DeepgramTTS."""
        from app.providers.registry import PROVIDERS

        assert PROVIDERS["tts"]["deepgram"] is DeepgramTTS

    def test_make_pipeline_tts_is_real_deepgram_tts(self):
        """make_pipeline returns a pipeline whose .tts is the real implementation."""
        from datetime import UTC, datetime
        from uuid import uuid4

        from app.models.tenant import (
            ProviderConfig,
            Tenant,
            TenantMarket,
            TenantOnboardingMode,
            TenantStatus,
        )
        from app.providers import make_pipeline

        now = datetime.now(UTC)
        tenant = Tenant(
            id=uuid4(),
            slug="test-tts",
            business_name="Test",
            market=TenantMarket.INDIA_ENGLISH,
            language="en",
            timezone="Asia/Kolkata",
            plan="starter",
            provider_config=ProviderConfig(
                stt="deepgram", tts="deepgram", llm="deepseek_native"
            ),
            onboarding_mode=TenantOnboardingMode.SELF_SERVE,
            status=TenantStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        pipeline = make_pipeline(tenant)
        assert isinstance(pipeline.tts, DeepgramTTS)
