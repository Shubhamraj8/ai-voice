"""Unit tests for the provider abstraction layer (ticket 2.06).

Tests verify:
- Registry resolves provider keys to the expected stub classes
- make_pipeline() returns a Pipeline with correct provider types
- Default India English stack is deepgram + deepgram + deepseek_native
- All stub classes raise NotImplementedError (not silent failures)
- validate_provider_config() accepts valid keys and rejects unknown ones
- MARKET_DEFAULTS covers all TenantMarket values
"""

from __future__ import annotations

from datetime import UTC, datetime
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
    def test_deepgram_stt_connect_raises(self):
        import asyncio

        with pytest.raises(NotImplementedError, match="DeepgramSTT"):
            asyncio.run(DeepgramSTT().connect("en"))

    def test_deepgram_tts_synthesize_raises(self):
        """DeepgramTTS is now a LIVE implementation (ticket 2.07).

        Without a DEEPGRAM_API_KEY it raises RuntimeError (not NotImplementedError).
        The old NotImplementedError was from the stub — now replaced by the real impl.
        """
        import asyncio

        async def _run():
            gen = DeepgramTTS().synthesize("hello", "aura-asteria-en", "en")
            await gen.__anext__()

        # Real impl raises RuntimeError when no API key is set
        with pytest.raises(RuntimeError, match="DeepgramTTS"):
            asyncio.run(_run())

    def test_deepseek_chat_raises(self):
        import asyncio

        with pytest.raises(NotImplementedError, match="DeepSeekNativeLLM"):
            asyncio.run(DeepSeekNativeLLM().chat([], [], max_tokens=10))

    def test_sarvam_stt_raises(self):
        import asyncio

        with pytest.raises(NotImplementedError, match="SarvamSTT"):
            asyncio.run(SarvamSTT().connect("hi"))

    def test_together_deepseek_raises(self):
        import asyncio

        with pytest.raises(NotImplementedError, match="TogetherDeepSeekLLM"):
            asyncio.run(TogetherDeepSeekLLM().chat([], []))

    def test_deepgram_enterprise_stt_raises(self):
        import asyncio

        with pytest.raises(NotImplementedError, match="DeepgramSTTEnterprise"):
            asyncio.run(DeepgramSTTEnterprise().connect("en"))

    def test_error_message_mentions_phase(self):
        """Stub errors must name the implementing phase."""
        import asyncio

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
