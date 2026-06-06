"""Known provider keys for tenant provider_config validation (ticket 3.03)."""

from app.errors import api_error
from app.models.tenant import ProviderConfig, TenantMarket

VALID_PROVIDERS: dict[str, frozenset[str]] = {
    "stt": frozenset(
        {
            "cartesia",
            "deepgram",
            "deepgram_baa",
            "sarvam",
            "openai_realtime",
        }
    ),
    "tts": frozenset(
        {
            "inworld",
            "deepgram",
            "deepgram_baa",
            "sarvam",
            "openai",
            "elevenlabs",
        }
    ),
    "llm": frozenset(
        {
            "deepseek_native",
            "together_deepseek",
            "openai_gpt5_mini",
        }
    ),
}

MARKET_DEFAULTS: dict[TenantMarket, ProviderConfig] = {
    TenantMarket.INDIA_ENGLISH: ProviderConfig(
        stt="cartesia", tts="inworld", llm="deepseek_native"
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
    return MARKET_DEFAULTS.get(
        market, MARKET_DEFAULTS[TenantMarket.INDIA_ENGLISH]
    ).model_copy()


def validate_provider_config(config: ProviderConfig) -> None:
    for field, allowed in VALID_PROVIDERS.items():
        value = getattr(config, field)
        if value not in allowed:
            raise api_error(
                400,
                "invalid_provider_config",
                f"Unknown {field} provider: {value}",
            )
