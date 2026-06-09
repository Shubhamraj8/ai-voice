"""Unit tests for provider layer (2.06), DeepgramTTS (2.07), DeepgramSTT (2.08)."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from app.models.tenant import (
    ProviderConfig,
    Tenant,
    TenantMarket,
    TenantOnboardingMode,
    TenantStatus,
)
from app.providers import (
    MARKET_DEFAULTS,
    PROVIDERS,
    Pipeline,
    make_pipeline,
    validate_provider_config,
)
from app.providers.deepgram_tts import (
    _DEFAULT_VOICE,
    _ENCODING,
    _MAX_RETRIES,
    _SAMPLE_RATE,
    VOICE_CATALOGUE,
)
from app.providers.stubs import (
    DeepgramSTT,
    DeepgramSTTEnterprise,
    DeepgramTTS,
    DeepgramTTSEnterprise,
    DeepSeekNativeLLM,
    SarvamSTT,
    SarvamTTS,
    TogetherDeepSeekLLM,
)
from openai import RateLimitError

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_tenant(
    stt: str,
    tts: str,
    llm: str,
    market: TenantMarket = TenantMarket.INDIA_ENGLISH,
) -> Tenant:
    now = datetime.now(UTC)
    return Tenant(
        id=uuid4(),
        slug="test-tenant",
        business_name="Test Business",
        market=market,
        language="en",
        timezone="Asia/Kolkata",
        plan="starter",
        provider_config=ProviderConfig(stt=stt, tts=tts, llm=llm),
        onboarding_mode=TenantOnboardingMode.SELF_SERVE,
        status=TenantStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )


# ---------------------------------------------------------------------------
# Registry structure tests
# ---------------------------------------------------------------------------


class TestRegistry:
    def test_providers_has_all_three_roles(self):
        assert "stt" in PROVIDERS
        assert "tts" in PROVIDERS
        assert "llm" in PROVIDERS

    def test_deepgram_stt_resolves(self):
        assert PROVIDERS["stt"]["deepgram"] is DeepgramSTT

    def test_deepgram_tts_resolves(self):
        assert PROVIDERS["tts"]["deepgram"] is DeepgramTTS

    def test_deepseek_native_resolves(self):
        assert PROVIDERS["llm"]["deepseek_native"] is DeepSeekNativeLLM

    def test_sarvam_stt_resolves(self):
        assert PROVIDERS["stt"]["sarvam"] is SarvamSTT

    def test_sarvam_tts_resolves(self):
        assert PROVIDERS["tts"]["sarvam"] is SarvamTTS

    def test_deepgram_baa_stt_resolves(self):
        assert PROVIDERS["stt"]["deepgram_baa"] is DeepgramSTTEnterprise

    def test_deepgram_baa_tts_resolves(self):
        assert PROVIDERS["tts"]["deepgram_baa"] is DeepgramTTSEnterprise

    def test_together_deepseek_resolves(self):
        assert PROVIDERS["llm"]["together_deepseek"] is TogetherDeepSeekLLM


# ---------------------------------------------------------------------------
# make_pipeline() tests
# ---------------------------------------------------------------------------


class TestMakePipeline:
    def test_returns_pipeline_instance(self):
        tenant = _make_tenant("deepgram", "deepgram", "deepseek_native")
        pipeline = make_pipeline(tenant)
        assert isinstance(pipeline, Pipeline)

    def test_india_english_default_stack(self):
        """Default India English stack: deepgram STT + deepgram TTS + deepseek LLM."""
        tenant = _make_tenant("deepgram", "deepgram", "deepseek_native")
        pipeline = make_pipeline(tenant)
        assert isinstance(pipeline.stt, DeepgramSTT)
        assert isinstance(pipeline.tts, DeepgramTTS)
        assert isinstance(pipeline.llm, DeepSeekNativeLLM)

    def test_us_hipaa_stack(self):
        """US HIPAA stack: deepgram_baa + deepgram_baa + together_deepseek."""
        tenant = _make_tenant(
            "deepgram_baa",
            "deepgram_baa",
            "together_deepseek",
            market=TenantMarket.US_HIPAA,
        )
        pipeline = make_pipeline(tenant)
        assert isinstance(pipeline.stt, DeepgramSTTEnterprise)
        assert isinstance(pipeline.tts, DeepgramTTSEnterprise)
        assert isinstance(pipeline.llm, TogetherDeepSeekLLM)

    def test_india_hindi_stack(self):
        """India Hindi stack: sarvam + sarvam + deepseek."""
        tenant = _make_tenant(
            "sarvam",
            "sarvam",
            "deepseek_native",
            market=TenantMarket.INDIA_HINDI,
        )
        pipeline = make_pipeline(tenant)
        assert isinstance(pipeline.stt, SarvamSTT)
        assert isinstance(pipeline.tts, SarvamTTS)
        assert isinstance(pipeline.llm, DeepSeekNativeLLM)

    def test_unknown_stt_key_raises_key_error(self):
        tenant = _make_tenant("nonexistent_stt", "deepgram", "deepseek_native")
        with pytest.raises(KeyError):
            make_pipeline(tenant)

    def test_each_call_creates_fresh_instances(self):
        """make_pipeline must not return the same object across calls."""
        tenant = _make_tenant("deepgram", "deepgram", "deepseek_native")
        p1 = make_pipeline(tenant)
        p2 = make_pipeline(tenant)
        assert p1.stt is not p2.stt
        assert p1.tts is not p2.tts
        assert p1.llm is not p2.llm


# ---------------------------------------------------------------------------
# Stub classes raise NotImplementedError
# ---------------------------------------------------------------------------


class TestStubsRaiseNotImplemented:
    def test_deepgram_stt_missing_api_key_raises(self):

        with (
            patch("app.providers.deepgram_stt.get_settings") as mock_settings,
            pytest.raises(RuntimeError, match="DEEPGRAM_API_KEY"),
        ):
            mock_settings.return_value.deepgram_api_key = ""
            asyncio.run(DeepgramSTT().connect("en"))

    def test_deepgram_tts_missing_api_key_raises(self):
        """DeepgramTTS is live (ticket 2.07) — fails fast when API key is absent."""

        async def _run():
            gen = DeepgramTTS().synthesize("hello", "aura-asteria-en", "en")
            await gen.__anext__()

        with (
            patch("app.providers.deepgram_tts.get_settings") as mock_settings,
            pytest.raises(RuntimeError, match="DEEPGRAM_API_KEY"),
        ):
            mock_settings.return_value.deepgram_api_key = ""
            asyncio.run(_run())

    def test_deepseek_missing_api_key_raises(self):
        with (
            patch("app.providers.deepseek_llm.get_settings") as mock_settings,
            pytest.raises(RuntimeError, match="DEEPSEEK_API_KEY"),
        ):
            mock_settings.return_value.deepseek_api_key = ""
            asyncio.run(DeepSeekNativeLLM().chat([], [], max_tokens=10))

    def test_sarvam_stt_raises(self):

        with pytest.raises(NotImplementedError, match="SarvamSTT"):
            asyncio.run(SarvamSTT().connect("hi"))

    def test_together_deepseek_raises(self):

        with pytest.raises(NotImplementedError, match="TogetherDeepSeekLLM"):
            asyncio.run(TogetherDeepSeekLLM().chat([], []))

    def test_deepgram_enterprise_stt_raises(self):

        with pytest.raises(NotImplementedError, match="DeepgramSTTEnterprise"):
            asyncio.run(DeepgramSTTEnterprise().connect("en"))

    def test_error_message_mentions_phase(self):
        """Stub errors must name the implementing phase."""

        try:
            asyncio.run(SarvamSTT().connect("hi"))
        except NotImplementedError as exc:
            assert "Phase" in str(exc)


# ---------------------------------------------------------------------------
# validate_provider_config tests
# ---------------------------------------------------------------------------


class TestValidateProviderConfig:
    def test_valid_india_english_config_passes(self):
        cfg = ProviderConfig(stt="deepgram", tts="deepgram", llm="deepseek_native")
        validate_provider_config(cfg)  # should not raise

    def test_valid_hipaa_config_passes(self):
        cfg = ProviderConfig(
            stt="deepgram_baa", tts="deepgram_baa", llm="together_deepseek"
        )
        validate_provider_config(cfg)  # should not raise

    def test_unknown_stt_raises_400(self):
        cfg = ProviderConfig(
            stt="unknown_vendor", tts="deepgram", llm="deepseek_native"
        )
        with pytest.raises(Exception) as exc_info:
            validate_provider_config(cfg)
        # api_error raises HTTPException with status 400
        assert exc_info.value.status_code == 400

    def test_unknown_llm_raises_400(self):
        cfg = ProviderConfig(stt="deepgram", tts="deepgram", llm="gpt_infinity")
        with pytest.raises(Exception) as exc_info:
            validate_provider_config(cfg)
        assert exc_info.value.status_code == 400


# ---------------------------------------------------------------------------
# MARKET_DEFAULTS tests
# ---------------------------------------------------------------------------


class TestMarketDefaults:
    def test_all_markets_have_defaults(self):
        for market in TenantMarket:
            assert market in MARKET_DEFAULTS, f"Missing default for {market}"

    def test_india_english_default_is_deepgram_stack(self):
        cfg = MARKET_DEFAULTS[TenantMarket.INDIA_ENGLISH]
        assert cfg.stt == "deepgram"
        assert cfg.tts == "deepgram"
        assert cfg.llm == "deepseek_native"

    def test_india_hindi_default_is_sarvam(self):
        cfg = MARKET_DEFAULTS[TenantMarket.INDIA_HINDI]
        assert cfg.stt == "sarvam"
        assert cfg.tts == "sarvam"

    def test_us_hipaa_default_uses_baa_providers(self):
        cfg = MARKET_DEFAULTS[TenantMarket.US_HIPAA]
        assert cfg.stt == "deepgram_baa"
        assert cfg.tts == "deepgram_baa"
        assert cfg.llm == "together_deepseek"

    def test_default_config_returns_copy(self):
        from app.providers import default_provider_config

        cfg1 = default_provider_config(TenantMarket.INDIA_ENGLISH)
        cfg2 = default_provider_config(TenantMarket.INDIA_ENGLISH)
        assert cfg1 is not cfg2  # must be independent copies


# ---------------------------------------------------------------------------
# DeepgramTTS helpers (ticket 2.07)
# ---------------------------------------------------------------------------


def _make_pcm_chunk(size: int = 320) -> bytes:
    return b"\x00" * size


async def _collect(gen: AsyncIterator[bytes]) -> list[bytes]:
    return [chunk async for chunk in gen]


# ---------------------------------------------------------------------------
# DeepgramTTS constants / catalogue (ticket 2.07)
# ---------------------------------------------------------------------------


class TestDeepgramTtsConstants:
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
# DeepgramTTS voice validation (ticket 2.07)
# ---------------------------------------------------------------------------


class TestDeepgramTtsVoiceValidation:
    async def test_unknown_voice_falls_back_to_default(self):
        async def _fake_synthesize_once(**kwargs: Any):
            assert kwargs["voice_id"] == _DEFAULT_VOICE
            yield _make_pcm_chunk()

        tts = DeepgramTTS()
        with (
            patch.object(tts, "_synthesize_once", side_effect=_fake_synthesize_once),
            patch("app.providers.deepgram_tts.get_settings") as mock_settings,
        ):
            mock_settings.return_value.deepgram_api_key = "test-key"
            chunks = await _collect(
                tts.synthesize("Hello!", voice_id="nonexistent-voice-en")
            )

        assert len(chunks) == 1

    async def test_empty_voice_id_uses_default(self):
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
        async def _fake_synthesize_once(**kwargs: Any):
            assert kwargs["voice_id"] == "aura-zeus-en"
            yield _make_pcm_chunk()

        tts = DeepgramTTS()
        with patch.object(tts, "_synthesize_once", side_effect=_fake_synthesize_once):
            chunks = await _collect(tts.synthesize("Hi!", voice_id="aura-zeus-en"))

        assert len(chunks) == 1


# ---------------------------------------------------------------------------
# DeepgramTTS retry + exponential back-off (ticket 2.07)
# ---------------------------------------------------------------------------


class TestDeepgramTtsRetryBackoff:
    async def test_retries_on_transient_error(self):
        call_count = 0

        async def _failing_synthesize_once(**kwargs: Any):
            nonlocal call_count
            call_count += 1
            raise RuntimeError("transient network error")
            yield

        tts = DeepgramTTS()
        with (
            patch.object(tts, "_synthesize_once", side_effect=_failing_synthesize_once),
            patch("app.providers.deepgram_tts.asyncio.sleep", new_callable=AsyncMock),
        ):
            with pytest.raises(RuntimeError, match="all 3 synthesis attempts failed"):
                await _collect(tts.synthesize("Hello"))

        assert call_count == _MAX_RETRIES

    async def test_succeeds_on_second_attempt(self):
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

        assert len(sleep_calls) == 2
        assert sleep_calls[0] == 0.5
        assert sleep_calls[1] == 1.0


# ---------------------------------------------------------------------------
# DeepgramTTS metrics (ticket 2.07)
# ---------------------------------------------------------------------------


class TestDeepgramTtsMetrics:
    async def test_char_count_matches_text_length(self):
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
        cost = 150 * 0.015 / 1000
        assert round(cost, 6) == 0.00225


# ---------------------------------------------------------------------------
# DeepgramTTS concise-reply budget (ticket 2.07)
# ---------------------------------------------------------------------------


class TestDeepgramTtsConciseReplyBudget:
    @pytest.mark.parametrize(
        "text",
        [
            "Hello, how can I help you today?",
            "Sure, I can help you with that. Please hold on.",
            "Your appointment has been scheduled for tomorrow at 10 AM.",
        ],
    )
    def test_short_utterances_within_budget(self, text: str):
        words = len(text.split())
        chars = len(text)
        assert words <= 25, f"Too many words: {words} > 25"
        assert chars <= 200, f"Too many chars: {chars} > 200"

    def test_budget_boundary_25_words(self):
        text = " ".join(["word"] * 25)
        assert len(text.split()) == 25
        assert len(text) <= 200

    def test_over_budget_200_words_detected(self):
        text = " ".join(["word"] * 200)
        assert len(text.split()) > 25


# ---------------------------------------------------------------------------
# DeepgramTTS API key guard (ticket 2.07)
# ---------------------------------------------------------------------------


class TestDeepgramTtsApiKeyGuard:
    async def test_missing_api_key_raises_runtime_error(self):
        tts = DeepgramTTS()
        with patch("app.providers.deepgram_tts.get_settings") as mock_settings:
            mock_settings.return_value.deepgram_api_key = ""
            with pytest.raises(RuntimeError, match="DEEPGRAM_API_KEY is not set"):
                await _collect(tts.synthesize("Hello"))


# ---------------------------------------------------------------------------
# DeepgramTTS streaming output (ticket 2.07)
# ---------------------------------------------------------------------------


class TestDeepgramTtsStreamingOutput:
    async def test_yields_multiple_chunks(self):
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
        greeting = "Hello, how can I help you today?"

        async def _once(**kwargs: Any):
            assert kwargs["text"] == greeting
            yield _make_pcm_chunk(640)

        tts = DeepgramTTS()
        with patch.object(tts, "_synthesize_once", side_effect=_once):
            chunks_received = await _collect(tts.synthesize(greeting))

        assert len(chunks_received) == 1
        assert len(chunks_received[0]) == 640


# ---------------------------------------------------------------------------
# DeepgramTTS SDK call shape (ticket 2.07)
# ---------------------------------------------------------------------------


class TestDeepgramTtsSdkCallShape:
    async def test_generate_stream_is_not_awaited(self):
        async def _fake_generate(**kwargs: Any):
            yield _make_pcm_chunk(320)
            yield _make_pcm_chunk(160)

        generate_mock = MagicMock(side_effect=lambda **kwargs: _fake_generate(**kwargs))
        mock_client = MagicMock()
        mock_client.speak.v1.audio.generate = generate_mock

        tts = DeepgramTTS()
        with (
            patch(
                "app.providers.deepgram_tts.AsyncDeepgramClient",
                return_value=mock_client,
            ),
            patch("app.providers.deepgram_tts.get_settings") as mock_settings,
        ):
            mock_settings.return_value.deepgram_api_key = "test-key"
            chunks = await _collect(tts.synthesize("Hello"))

        assert len(chunks) == 2
        generate_mock.assert_called_once()
        call_kwargs = generate_mock.call_args.kwargs
        assert call_kwargs["text"] == "Hello"
        assert call_kwargs["model"] == _DEFAULT_VOICE
        assert call_kwargs["encoding"] == _ENCODING
        assert call_kwargs["sample_rate"] == _SAMPLE_RATE


# ---------------------------------------------------------------------------
# DeepgramSTT helpers (ticket 2.08)
# ---------------------------------------------------------------------------


async def _collect_transcripts(gen: AsyncIterator) -> list:
    from app.providers.base import Transcript

    return [t async for t in gen if isinstance(t, Transcript)]


def _make_listen_results(
    *,
    text: str,
    is_final: bool,
    confidence: float = 0.92,
):
    from deepgram.listen.v1.types import (
        ListenV1Results,
        ListenV1ResultsChannel,
        ListenV1ResultsChannelAlternativesItem,
        ListenV1ResultsChannelAlternativesItemWordsItem,
        ListenV1ResultsMetadata,
        ListenV1ResultsMetadataModelInfo,
    )

    words = [
        ListenV1ResultsChannelAlternativesItemWordsItem(
            word=token,
            start=float(i),
            end=float(i) + 0.25,
            confidence=confidence,
        )
        for i, token in enumerate(text.split() or ["silence"])
    ]
    alternative = ListenV1ResultsChannelAlternativesItem(
        transcript=text,
        confidence=confidence,
        words=words,
    )
    return ListenV1Results(
        channel_index=[0, 1],
        duration=1.0,
        start=0.0,
        is_final=is_final,
        speech_final=is_final,
        channel=ListenV1ResultsChannel(alternatives=[alternative]),
        metadata=ListenV1ResultsMetadata(
            request_id="test-request-id",
            model_info=ListenV1ResultsMetadataModelInfo(
                name="nova-3",
                version="1.0",
                arch="nova",
            ),
            model_uuid="test-model-uuid",
        ),
    )


async def _pcm_chunks(*chunks: bytes):
    for chunk in chunks:
        yield chunk


class _FakeConnectCm:
    def __init__(self, socket: AsyncMock) -> None:
        self._socket = socket

    async def __aenter__(self) -> AsyncMock:
        return self._socket

    async def __aexit__(self, *args: object) -> None:
        return None


# ---------------------------------------------------------------------------
# DeepgramSTT constants (ticket 2.08)
# ---------------------------------------------------------------------------


class TestDeepgramSttConstants:
    def test_model_is_nova3(self):
        from app.providers.deepgram_stt import _MODEL

        assert _MODEL == "nova-3"

    def test_sample_rate_is_16000(self):
        from app.providers.deepgram_stt import _SAMPLE_RATE

        assert _SAMPLE_RATE == 16000

    def test_endpointing_is_300ms(self):
        from app.providers.deepgram_stt import _ENDPOINTING_MS

        assert _ENDPOINTING_MS == 300

    def test_normalize_language_maps_en_in(self):
        from app.providers.deepgram_stt import _normalize_language

        assert _normalize_language("en-IN") == "en"


# ---------------------------------------------------------------------------
# DeepgramSTT message parsing (ticket 2.08)
# ---------------------------------------------------------------------------


class TestDeepgramSttParseMessage:
    def test_partial_transcript_parsed(self):
        stt = DeepgramSTT()
        msg = _make_listen_results(text="hello", is_final=False, confidence=0.7)
        t = stt._parse_message(msg)
        assert t is not None
        assert t.text == "hello"
        assert t.is_final is False
        assert t.confidence == 0.7

    def test_final_transcript_parsed(self):
        stt = DeepgramSTT()
        msg = _make_listen_results(text="hello world", is_final=True, confidence=0.95)
        t = stt._parse_message(msg)
        assert t is not None
        assert t.is_final is True
        assert t.confidence == 0.95

    def test_empty_partial_skipped(self):
        stt = DeepgramSTT()
        msg = _make_listen_results(text="   ", is_final=False)
        assert stt._parse_message(msg) is None


# ---------------------------------------------------------------------------
# DeepgramSTT streaming (ticket 2.08)
# ---------------------------------------------------------------------------


class TestDeepgramSttStreaming:
    async def test_partial_before_final(self):
        partial = _make_listen_results(text="hel", is_final=False)
        final = _make_listen_results(text="hello", is_final=True, confidence=0.91)

        recv_queue = [partial, final]

        def _recv_messages():
            if recv_queue:
                return recv_queue.pop(0)
            raise TimeoutError()

        mock_socket = AsyncMock()
        mock_socket.recv = AsyncMock(side_effect=_recv_messages)
        mock_socket.send_media = AsyncMock()
        mock_socket.send_finalize = AsyncMock()
        mock_socket.send_close_stream = AsyncMock()

        mock_client = MagicMock()
        mock_client.listen.v1.connect = MagicMock(
            return_value=_FakeConnectCm(mock_socket)
        )

        stt = DeepgramSTT()
        with (
            patch(
                "app.providers.deepgram_stt.AsyncDeepgramClient",
                return_value=mock_client,
            ),
            patch("app.providers.deepgram_stt.get_settings") as mock_settings,
        ):
            mock_settings.return_value.deepgram_api_key = "test-key"
            await stt.connect("en")
            transcripts = await _collect_transcripts(
                stt.stream(_pcm_chunks(b"\x00\x00" * 320))
            )
            await stt.close()

        assert len(transcripts) == 2
        assert transcripts[0].is_final is False
        assert transcripts[1].is_final is True
        assert transcripts[1].confidence >= 0.85
        connect_kwargs = mock_client.listen.v1.connect.call_args.kwargs
        assert connect_kwargs["model"] == "nova-3"
        assert connect_kwargs["language"] == "en"
        assert connect_kwargs["interim_results"] is True
        assert connect_kwargs["smart_format"] is True
        assert connect_kwargs["endpointing"] == 300
        assert connect_kwargs["vad_events"] is True

    async def test_stream_requires_connect(self):
        stt = DeepgramSTT()
        with pytest.raises(RuntimeError, match="connect\\(\\) must be called"):
            await _collect_transcripts(stt.stream(_pcm_chunks(b"\x00")))

    async def test_reconnect_on_close_code_1006(self):
        from websockets.exceptions import ConnectionClosed
        from websockets.frames import Close

        partial = _make_listen_results(text="hi", is_final=False)
        final = _make_listen_results(text="hi there", is_final=True, confidence=0.9)
        disconnect = ConnectionClosed(Close(1006, "abnormal"), None)

        sockets: list[AsyncMock] = []

        failing_socket = AsyncMock()
        failing_socket.recv = AsyncMock(side_effect=TimeoutError)
        failing_socket.send_media = AsyncMock(side_effect=disconnect)
        failing_socket.send_finalize = AsyncMock()
        failing_socket.send_close_stream = AsyncMock()
        sockets.append(failing_socket)

        recovery_queue = [partial, final]

        def _recovery_recv():
            if recovery_queue:
                return recovery_queue.pop(0)
            raise TimeoutError()

        recovery_socket = AsyncMock()
        recovery_socket.recv = AsyncMock(side_effect=_recovery_recv)
        recovery_socket.send_media = AsyncMock()
        recovery_socket.send_finalize = AsyncMock()
        recovery_socket.send_close_stream = AsyncMock()
        sockets.append(recovery_socket)

        socket_iter = iter(sockets)

        def _make_cm(*args: Any, **kwargs: Any) -> _FakeConnectCm:
            return _FakeConnectCm(next(socket_iter))

        mock_client = MagicMock()
        mock_client.listen.v1.connect = MagicMock(side_effect=_make_cm)

        stt = DeepgramSTT()
        with (
            patch(
                "app.providers.deepgram_stt.AsyncDeepgramClient",
                return_value=mock_client,
            ),
            patch("app.providers.deepgram_stt.get_settings") as mock_settings,
        ):
            mock_settings.return_value.deepgram_api_key = "test-key"
            await stt.connect("en")
            transcripts = await _collect_transcripts(
                stt.stream(_pcm_chunks(b"\x00\x00" * 320))
            )
            await stt.close()

        assert mock_client.listen.v1.connect.call_count == 2
        assert any(t.is_final for t in transcripts)


# ---------------------------------------------------------------------------
# DeepSeekNativeLLM (ticket 2.09)
# ---------------------------------------------------------------------------


def _make_chat_completion(
    *,
    text: str = "Hello! I am your voice assistant.",
    tool_calls: list | None = None,
    cached_tokens: int = 0,
) -> MagicMock:
    message = MagicMock()
    message.content = text
    message.tool_calls = tool_calls

    usage = SimpleNamespace(
        prompt_tokens=42,
        completion_tokens=18,
        total_tokens=60,
        prompt_tokens_details=SimpleNamespace(cached_tokens=cached_tokens),
    )

    choice = MagicMock()
    choice.message = message

    completion = MagicMock()
    completion.choices = [choice]
    completion.usage = usage
    completion.model = "deepseek-v4-flash"
    return completion


class TestDeepSeekLlmConstants:
    def test_default_model_is_v4_flash(self):
        from app.providers.deepseek_llm import _DEFAULT_MODEL

        assert _DEFAULT_MODEL == "deepseek-v4-flash"


class TestDeepSeekLlmChat:
    async def test_chat_returns_text_response(self):
        from app.providers.base import Message

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=_make_chat_completion()
        )

        llm = DeepSeekNativeLLM()
        with (
            patch(
                "app.providers.deepseek_llm.AsyncOpenAI",
                return_value=mock_client,
            ),
            patch("app.providers.deepseek_llm.get_settings") as mock_settings,
        ):
            mock_settings.return_value.deepseek_api_key = "test-key"
            mock_settings.return_value.deepseek_base_url = "https://api.deepseek.com"
            mock_settings.return_value.deepseek_model = "deepseek-v4-flash"
            mock_settings.return_value.deepseek_timeout_s = 30.0
            response = await llm.chat(
                messages=[Message(role="user", content="Hello, who are you?")],
                tools=[],
                max_tokens=100,
            )

        assert "voice assistant" in response.text
        assert response.tool_calls == []
        assert response.usage["prompt_tokens"] == 42
        mock_client.chat.completions.create.assert_awaited_once()
        call_kwargs = mock_client.chat.completions.create.await_args.kwargs
        assert call_kwargs["model"] == "deepseek-v4-flash"
        assert call_kwargs["max_tokens"] == 100

    async def test_tool_calling_parsed(self):
        from app.providers.base import Message

        tool_call = MagicMock()
        tool_call.id = "call_123"
        tool_call.function.name = "get_weather"
        tool_call.function.arguments = '{"city": "Mumbai"}'

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=_make_chat_completion(text="", tool_calls=[tool_call])
        )

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]

        llm = DeepSeekNativeLLM()
        with (
            patch(
                "app.providers.deepseek_llm.AsyncOpenAI",
                return_value=mock_client,
            ),
            patch("app.providers.deepseek_llm.get_settings") as mock_settings,
        ):
            mock_settings.return_value.deepseek_api_key = "test-key"
            mock_settings.return_value.deepseek_base_url = "https://api.deepseek.com"
            mock_settings.return_value.deepseek_model = "deepseek-v4-flash"
            mock_settings.return_value.deepseek_timeout_s = 30.0
            response = await llm.chat(
                messages=[Message(role="user", content="Weather in Mumbai?")],
                tools=tools,
            )

        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].name == "get_weather"
        assert response.tool_calls[0].arguments == {"city": "Mumbai"}
        assert mock_client.chat.completions.create.await_args.kwargs["tools"] == tools

    async def test_cache_hit_tokens_in_usage(self):
        from app.providers.base import Message

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=_make_chat_completion(cached_tokens=35)
        )

        llm = DeepSeekNativeLLM()
        with (
            patch(
                "app.providers.deepseek_llm.AsyncOpenAI",
                return_value=mock_client,
            ),
            patch("app.providers.deepseek_llm.get_settings") as mock_settings,
        ):
            mock_settings.return_value.deepseek_api_key = "test-key"
            mock_settings.return_value.deepseek_base_url = "https://api.deepseek.com"
            mock_settings.return_value.deepseek_model = "deepseek-v4-flash"
            mock_settings.return_value.deepseek_timeout_s = 30.0
            response = await llm.chat(
                messages=[
                    Message(role="system", content="You are a helpful assistant."),
                    Message(role="user", content="Hello again."),
                ],
                tools=[],
            )

        assert response.usage["cached_tokens"] == 35

    async def test_rate_limit_retries_with_backoff(self):
        from app.providers.base import Message

        rate_error = RateLimitError(
            message="rate limit",
            response=MagicMock(headers={}),
            body=None,
        )

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=[rate_error, _make_chat_completion(text="Recovered.")]
        )

        llm = DeepSeekNativeLLM()
        with (
            patch(
                "app.providers.deepseek_llm.AsyncOpenAI",
                return_value=mock_client,
            ),
            patch("app.providers.deepseek_llm.get_settings") as mock_settings,
            patch(
                "app.providers.deepseek_llm.asyncio.sleep",
                new_callable=AsyncMock,
            ) as mock_sleep,
        ):
            mock_settings.return_value.deepseek_api_key = "test-key"
            mock_settings.return_value.deepseek_base_url = "https://api.deepseek.com"
            mock_settings.return_value.deepseek_model = "deepseek-v4-flash"
            mock_settings.return_value.deepseek_timeout_s = 30.0
            response = await llm.chat(
                messages=[Message(role="user", content="Hello")],
                tools=[],
            )

        assert response.text == "Recovered."
        assert mock_client.chat.completions.create.await_count == 2
        mock_sleep.assert_awaited_once()
