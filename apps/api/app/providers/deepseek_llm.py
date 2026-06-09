"""DeepSeek V4 Flash LLM provider — ticket 2.09.

Implements the LLMProvider protocol via the DeepSeek OpenAI-compatible API
using the ``openai`` AsyncOpenAI client.

Key features
------------
- Model: ``deepseek-v4-flash`` (configurable via ``DEEPSEEK_MODEL``)
- OpenAI-compatible tool / function calling
- Prompt caching — keep the system prompt prefix stable across calls so
  DeepSeek's cache discount applies (logged via ``cached_tokens`` in usage)
- Retry with exponential back-off on rate limits (429) and transient errors
- Per-call token usage logging for cost tracking

Billing (deepseek-v4-flash, per 1M tokens)
------------------------------------------
- Input cache hit:  $0.0028
- Input cache miss: $0.14
- Output:           $0.28
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any

import structlog
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    RateLimitError,
)

from app.config import get_settings
from app.providers.base import LLMResponse, Message, ToolCall

log = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_BASE_URL = "https://api.deepseek.com"
_DEFAULT_MODEL = "deepseek-v4-flash"
_MAX_RETRIES = 3
_BACKOFF_BASE = 0.5
_RETRYABLE_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------


class DeepSeekNativeLLM:
    """DeepSeek V4 Flash via the native OpenAI-compatible API.

    Satisfies the LLMProvider protocol (app/providers/base.py).

    Usage::

        llm = DeepSeekNativeLLM()
        response = await llm.chat(
            messages=[Message(role="user", content="Hello!")],
            tools=[],
            max_tokens=200,
        )
    """

    async def chat(
        self,
        messages: list[Message],
        tools: list[dict],
        max_tokens: int = 200,
    ) -> LLMResponse:
        """Run a chat completion with optional tool calling."""
        settings = get_settings()
        api_key = settings.deepseek_api_key
        if not api_key:
            raise RuntimeError(
                "DEEPSEEK_API_KEY is not set — cannot run chat completion. "
                "Set it in .env or Render environment variables."
            )

        client = AsyncOpenAI(
            api_key=api_key,
            base_url=settings.deepseek_base_url or _DEFAULT_BASE_URL,
            timeout=settings.deepseek_timeout_s,
        )

        api_messages = _to_api_messages(messages)
        kwargs: dict[str, Any] = {
            "model": settings.deepseek_model or _DEFAULT_MODEL,
            "messages": api_messages,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools

        attempt = 0
        last_error: Exception | None = None
        t_start = time.monotonic()

        while attempt < _MAX_RETRIES:
            attempt += 1
            try:
                response = await client.chat.completions.create(**kwargs)
                return _parse_response(response, t_start=t_start, attempt=attempt)
            except RateLimitError as exc:
                last_error = exc
                if attempt < _MAX_RETRIES:
                    delay = _backoff_delay(exc, attempt)
                    log.warning(
                        "deepseek_llm.rate_limit",
                        attempt=attempt,
                        delay_s=delay,
                        error=str(exc),
                    )
                    await asyncio.sleep(delay)
                    continue
                raise RuntimeError(
                    f"DeepSeekNativeLLM: rate limit persisted after "
                    f"{_MAX_RETRIES} attempts."
                ) from exc
            except (APITimeoutError, APIConnectionError) as exc:
                last_error = exc
                if attempt < _MAX_RETRIES:
                    delay = _BACKOFF_BASE * (2 ** (attempt - 1))
                    log.warning(
                        "deepseek_llm.retry",
                        attempt=attempt,
                        delay_s=delay,
                        error=str(exc),
                    )
                    await asyncio.sleep(delay)
                    continue
                raise RuntimeError(
                    f"DeepSeekNativeLLM: request failed after "
                    f"{_MAX_RETRIES} attempts. Last error: {exc}"
                ) from exc
            except APIStatusError as exc:
                if exc.status_code not in _RETRYABLE_STATUS_CODES:
                    raise
                last_error = exc
                if attempt < _MAX_RETRIES:
                    delay = _backoff_delay(exc, attempt)
                    log.warning(
                        "deepseek_llm.retry",
                        attempt=attempt,
                        delay_s=delay,
                        status_code=exc.status_code,
                        error=str(exc),
                    )
                    await asyncio.sleep(delay)
                    continue
                raise RuntimeError(
                    f"DeepSeekNativeLLM: API error {exc.status_code} after "
                    f"{_MAX_RETRIES} attempts."
                ) from exc

        raise RuntimeError(
            f"DeepSeekNativeLLM: all {_MAX_RETRIES} attempts failed. "
            f"Last error: {last_error}"
        ) from last_error


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_api_messages(messages: list[Message]) -> list[dict[str, Any]]:
    """Convert provider Message models to OpenAI chat message dicts."""
    api_messages: list[dict[str, Any]] = []
    for message in messages:
        payload: dict[str, Any] = {
            "role": message.role,
            "content": message.content,
        }
        if message.tool_call_id:
            payload["tool_call_id"] = message.tool_call_id
        if message.name:
            payload["name"] = message.name
        api_messages.append(payload)
    return api_messages


def _parse_response(response: Any, *, t_start: float, attempt: int) -> LLMResponse:
    """Map an OpenAI-style completion to LLMResponse + structured logs."""
    choice = response.choices[0]
    message = choice.message
    text = message.content or ""

    tool_calls: list[ToolCall] = []
    if message.tool_calls:
        for call in message.tool_calls:
            raw_args = call.function.arguments or "{}"
            try:
                arguments = json.loads(raw_args)
            except json.JSONDecodeError:
                arguments = {"raw": raw_args}
            tool_calls.append(
                ToolCall(
                    id=call.id,
                    name=call.function.name,
                    arguments=arguments,
                )
            )

    usage = _extract_usage(response.usage)
    total_ms = round((time.monotonic() - t_start) * 1000)

    log.info(
        "deepseek_llm.completed",
        model=getattr(response, "model", None),
        attempt=attempt,
        total_ms=total_ms,
        prompt_tokens=usage.get("prompt_tokens", 0),
        completion_tokens=usage.get("completion_tokens", 0),
        cached_tokens=usage.get("cached_tokens", 0),
        cache_hit=usage.get("cached_tokens", 0) > 0,
        tool_calls=len(tool_calls),
    )

    return LLMResponse(text=text, tool_calls=tool_calls, usage=usage)


def _extract_usage(usage: Any) -> dict[str, int]:
    """Normalise token usage, including DeepSeek/OpenAI cache-hit metadata."""
    if usage is None:
        return {}

    result: dict[str, int] = {
        "prompt_tokens": int(getattr(usage, "prompt_tokens", 0) or 0),
        "completion_tokens": int(getattr(usage, "completion_tokens", 0) or 0),
        "total_tokens": int(getattr(usage, "total_tokens", 0) or 0),
    }

    details = getattr(usage, "prompt_tokens_details", None)
    if details is not None:
        cached = getattr(details, "cached_tokens", None)
        if cached is not None:
            result["cached_tokens"] = int(cached)

    # Some SDK versions expose cache fields on usage directly.
    for key in ("cached_tokens", "prompt_cache_hit_tokens"):
        value = getattr(usage, key, None)
        if value is not None:
            result["cached_tokens"] = int(value)

    return result


def _backoff_delay(exc: Exception, attempt: int) -> float:
    """Compute retry delay, honouring Retry-After when present."""
    retry_after: float | None = None
    response = getattr(exc, "response", None)
    if response is not None:
        header = response.headers.get("retry-after")
        if header:
            try:
                retry_after = float(header)
            except ValueError:
                retry_after = None
    if retry_after is not None:
        return retry_after
    return _BACKOFF_BASE * (2 ** (attempt - 1))
