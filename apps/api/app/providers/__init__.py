"""Provider abstraction layer (ticket 2.06, design.md §4).

Public API — import from here, not from submodules directly.

    from app.providers import (
        STTProvider, TTSProvider, LLMProvider,
        Transcript, Message, ToolCall, LLMResponse,
        Pipeline, make_pipeline,
        PROVIDERS, MARKET_DEFAULTS,
    )
"""

from app.providers.base import (
    LLMProvider,
    LLMResponse,
    Message,
    STTProvider,
    ToolCall,
    Transcript,
    TTSProvider,
)
from app.providers.registry import (
    MARKET_DEFAULTS,
    PROVIDERS,
    VALID_PROVIDERS,
    Pipeline,
    default_provider_config,
    make_pipeline,
    validate_provider_config,
)

__all__ = [
    # Protocols
    "STTProvider",
    "TTSProvider",
    "LLMProvider",
    # Shared models
    "Transcript",
    "Message",
    "ToolCall",
    "LLMResponse",
    # Pipeline
    "Pipeline",
    "make_pipeline",
    # Registry helpers
    "PROVIDERS",
    "VALID_PROVIDERS",
    "MARKET_DEFAULTS",
    "default_provider_config",
    "validate_provider_config",
]
