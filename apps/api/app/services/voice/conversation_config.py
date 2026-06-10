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

# Synthetic first-turn prompt queued when the caller connects.
CONNECT_GREETING_PROMPT = (
    "The caller just connected. Greet them warmly in one short sentence."
)


def build_llm_context() -> LLMContext:
    """Return a fresh LLM context seeded with the hardcoded system prompt."""

    return LLMContext(
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            }
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
