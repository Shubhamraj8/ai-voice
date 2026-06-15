"""Conversation settings for the full voice pipeline (ticket 2.12)."""

from __future__ import annotations

from pipecat.processors.aggregators.llm_context import LLMContext

SYSTEM_PROMPT = (
    "You are a helpful AI receptionist for a business. "
    "Keep every reply under 25 words. Be warm, clear, and concise."
)

# Last N user+assistant pairs kept in LLM context (plus the system prompt).
MAX_CONVERSATION_TURNS = 10

# Hard cap on LLM output tokens — keeps TTS cost and latency low.
MAX_LLM_OUTPUT_TOKENS = 200

# Spoken immediately on call connect (ticket 2.16). Static so it plays within
# 800ms — TTS only, no LLM round-trip — and matches the receptionist persona.
# Per-agent greetings (derived from the agent's starter_prompt) arrive with the
# tenant/agent lookup in 3.09.
GREETING_TEXT = "Hello! Thanks for calling. How can I help you today?"


def build_llm_context(system_prompt: str | None = None) -> LLMContext:
    """Return a fresh LLM context seeded with the agent's system prompt and the
    spoken greeting, so the model continues coherently after the static greeting.

    Falls back to the default ``SYSTEM_PROMPT`` when no per-agent prompt is given
    (ticket 3.10).
    """

    return LLMContext(
        messages=[
            {"role": "system", "content": system_prompt or SYSTEM_PROMPT},
            {"role": "assistant", "content": GREETING_TEXT},
        ]
    )


def trim_conversation_history(
    context: LLMContext,
    *,
    max_turns: int = MAX_CONVERSATION_TURNS,
) -> None:
    """Keep the system prompt and the most recent ``max_turns`` user/assistant pairs."""

    messages = context.messages

    system_messages = [
        message for message in messages if message.get("role") == "system"
    ]

    dialogue = [message for message in messages if message.get("role") != "system"]

    max_dialogue_messages = max_turns * 2

    if len(dialogue) <= max_dialogue_messages:
        return

    context.set_messages(system_messages + dialogue[-max_dialogue_messages:])
