"""Provider protocols and shared Pydantic models (ticket 2.06, design.md §4).

The voice pipeline always talks to these abstract interfaces — never to concrete
vendor SDKs directly.  Concrete classes are resolved at agent-spawn time via the
provider registry (registry.py).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    pass

# ---------------------------------------------------------------------------
# Shared data models
# ---------------------------------------------------------------------------


class Transcript(BaseModel):
    """Single STT result emitted by an STTProvider stream."""

    text: str
    is_final: bool
    confidence: float = Field(ge=0.0, le=1.0)
    language: str | None = None


class Message(BaseModel):
    """One LLM conversation turn."""

    role: str  # 'system' | 'user' | 'assistant' | 'tool'
    content: str
    tool_call_id: str | None = None  # set when role == 'tool'
    name: str | None = None  # tool name when role == 'tool'


class ToolCall(BaseModel):
    """A tool invocation requested by the LLM."""

    id: str
    name: str
    arguments: dict  # JSON-decoded args


class LLMResponse(BaseModel):
    """Full response from an LLMProvider.chat() call."""

    text: str
    tool_calls: list[ToolCall] = Field(default_factory=list)
    usage: dict = Field(default_factory=dict)  # tokens in/out/cached


# ---------------------------------------------------------------------------
# Provider protocols
# ---------------------------------------------------------------------------


@runtime_checkable
class STTProvider(Protocol):
    """Speech-to-text: streams audio bytes → Transcript events."""

    async def connect(self, language: str) -> None:
        """Open the upstream connection / websocket for the given language."""
        ...

    async def stream(
        self,
        audio_chunks: AsyncIterator[bytes],
    ) -> AsyncIterator[Transcript]:
        """Consume raw audio chunks; yield Transcript events (partial + final)."""
        ...

    async def close(self) -> None:
        """Tear down the upstream connection gracefully."""
        ...


@runtime_checkable
class TTSProvider(Protocol):
    """Text-to-speech: synthesizes text → audio byte chunks."""

    async def synthesize(
        self,
        text: str,
        voice_id: str,
        language: str,
    ) -> AsyncIterator[bytes]:
        """Synthesize *text* with the given voice and language.

        Yields raw audio bytes (PCM/mu-law/ogg — format is provider-specific;
        callers must know what to expect from the concrete impl).
        """
        ...


@runtime_checkable
class LLMProvider(Protocol):
    """Large-language-model: chat completions with optional tool calling."""

    async def chat(
        self,
        messages: list[Message],
        tools: list[dict],
        max_tokens: int = 200,
    ) -> LLMResponse:
        """Run a chat completion.

        Args:
            messages: Full conversation history including system prompt.
            tools:    OpenAI-compatible tool schemas (JSON-serialisable dicts).
            max_tokens: Hard cap on output tokens (kept low for cost control).

        Returns:
            LLMResponse with text and/or tool_calls.
        """
        ...
