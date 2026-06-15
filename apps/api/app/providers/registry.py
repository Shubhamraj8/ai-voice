"""Provider registry and pipeline factory (ticket 2.06, design.md §4).

PROVIDERS maps role → provider-key → concrete class.
make_pipeline() resolves a tenant's provider_config to live instances.

The validation helpers (VALID_PROVIDERS, MARKET_DEFAULTS, ...) are used by
the internal-tenant API (ticket 3.03) to reject unknown provider keys before
they ever reach make_pipeline().
"""

from __future__ import annotations

from dataclasses import dataclass

from app.errors import api_error
from app.models.tenant import ProviderConfig, Tenant, TenantMarket
from app.providers.base import LLMProvider, STTProvider, TTSProvider

# ---------------------------------------------------------------------------
# Class-level registry  (design.md §4 layout)
# ---------------------------------------------------------------------------
# Each leaf value is a *class* (not an instance).  make_pipeline() calls it
# with no arguments to create a fresh instance per call session.
# ---------------------------------------------------------------------------
from app.providers.deepgram_stt import DeepgramSTT  # LIVE — ticket 2.08
from app.providers.deepgram_tts import DeepgramTTS  # LIVE — ticket 2.07
from app.providers.deepseek_llm import DeepSeekNativeLLM  # LIVE — ticket 2.09
from app.providers.stubs import (  # noqa: E402  (after model imports)
    DeepgramSTTEnterprise,
    DeepgramTTSEnterprise,
    ElevenLabsTTS,
    OpenAIGPT5MiniLLM,
    OpenAIRealtimeSTT,
    OpenAITTS,
    SarvamSTT,
    SarvamTTS,
    TogetherDeepSeekLLM,
)

PROVIDERS: dict[str, dict[str, type]] = {
    "stt": {
        "deepgram": DeepgramSTT,
        "deepgram_baa": DeepgramSTTEnterprise,
        "sarvam": SarvamSTT,
        "openai_realtime": OpenAIRealtimeSTT,
        # Legacy keys kept for backward-compat with existing tenant rows
        "cartesia": DeepgramSTT,  # remapped — cartesia removed in v1.2
    },
    "tts": {
        "deepgram": DeepgramTTS,
        "deepgram_baa": DeepgramTTSEnterprise,
        "sarvam": SarvamTTS,
        "openai": OpenAITTS,
        "elevenlabs": ElevenLabsTTS,
        # Legacy keys
        "inworld": DeepgramTTS,  # remapped — inworld removed in v1.2
    },
    "llm": {
        "deepseek_native": DeepSeekNativeLLM,
        "together_deepseek": TogetherDeepSeekLLM,
        "openai_gpt5_mini": OpenAIGPT5MiniLLM,
    },
}

# ---------------------------------------------------------------------------
# Validation helpers  (used by internal-tenant API — ticket 3.03)
# ---------------------------------------------------------------------------

VALID_PROVIDERS: dict[str, frozenset[str]] = {
    role: frozenset(keys) for role, keys in PROVIDERS.items()
}

MARKET_DEFAULTS: dict[TenantMarket, ProviderConfig] = {
    TenantMarket.INDIA_ENGLISH: ProviderConfig(
        stt="deepgram", tts="deepgram", llm="deepseek_native"
    ),
    TenantMarket.INDIA_HINDI: ProviderConfig(
        stt="sarvam", tts="sarvam", llm="deepseek_native"
    ),
    TenantMarket.US_ENGLISH: ProviderConfig(
        stt="deepgram", tts="deepgram", llm="deepseek_native"
    ),
    TenantMarket.US_HIPAA: ProviderConfig(
        stt="deepgram_baa", tts="deepgram_baa", llm="together_deepseek"
    ),
    TenantMarket.GLOBAL_ENGLISH: ProviderConfig(
        stt="deepgram", tts="deepgram", llm="deepseek_native"
    ),
}


def default_provider_config(market: TenantMarket) -> ProviderConfig:
    """Return a copy of the default ProviderConfig for *market*."""
    return MARKET_DEFAULTS.get(
        market, MARKET_DEFAULTS[TenantMarket.INDIA_ENGLISH]
    ).model_copy()


def validate_provider_config(config: ProviderConfig) -> None:
    """Raise a 400 api_error if any provider key in *config* is unknown."""
    for field, allowed in VALID_PROVIDERS.items():
        value = getattr(config, field)
        if value not in allowed:
            raise api_error(
                400,
                "invalid_provider_config",
                f"Unknown {field} provider: {value!r}",
            )


# ---------------------------------------------------------------------------
# Pipeline container + factory  (design.md §4 — make_pipeline)
# ---------------------------------------------------------------------------


@dataclass
class Pipeline:
    """Resolved provider instances for a single tenant call session."""

    stt: STTProvider
    tts: TTSProvider
    llm: LLMProvider


def make_pipeline(tenant: Tenant) -> Pipeline:
    """Resolve a tenant's provider_config and return a Pipeline instance.

    Each call to make_pipeline() creates *fresh* provider instances — do not
    share Pipeline objects across concurrent calls.

    Args:
        tenant: Fully-loaded Tenant model (must have provider_config set).

    Returns:
        Pipeline with stt, tts, and llm provider instances.

    Raises:
        KeyError: If a provider key is not in the PROVIDERS registry.
                  This should never happen in production because
                  validate_provider_config() guards writes; it would indicate
                  a registry desync.
    """
    cfg = tenant.provider_config
    stt = PROVIDERS["stt"][cfg.stt]()
    tts = PROVIDERS["tts"][cfg.tts]()
    llm = PROVIDERS["llm"][cfg.llm]()
    return Pipeline(stt=stt, tts=tts, llm=llm)


# Provider classes with a real implementation (the rest are Phase 3/4 stubs).
LIVE_PROVIDER_CLASSES: frozenset[type] = frozenset(
    {DeepgramSTT, DeepgramTTS, DeepSeekNativeLLM}
)


def ensure_live_providers(config: ProviderConfig) -> None:
    """Raise if any provider in *config* is still a stub (ticket 3.10).

    Checked at pipeline construction so a misconfigured tenant fails clearly up
    front rather than mid-call.
    """
    for role in ("stt", "tts", "llm"):
        key = getattr(config, role)
        cls = PROVIDERS[role][key]
        if cls not in LIVE_PROVIDER_CLASSES:
            raise ValueError(
                f"Provider {role}={key!r} ({cls.__name__}) is not implemented "
                "yet (stub) — cannot build a live pipeline."
            )
