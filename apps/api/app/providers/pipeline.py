"""Voice pipeline container (ticket 2.06).

Pipeline holds the three resolved provider instances for one tenant's call.
It is created by make_pipeline() in registry.py and passed to the Pipecat
agent worker.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.providers.base import LLMProvider, STTProvider, TTSProvider


@dataclass
class Pipeline:
    """Resolved provider instances for a single tenant call session.

    Attributes:
        stt: Speech-to-text provider instance.
        tts: Text-to-speech provider instance.
        llm: Large-language-model provider instance.
    """

    stt: STTProvider
    tts: TTSProvider
    llm: LLMProvider
