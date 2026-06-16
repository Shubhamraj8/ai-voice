"""Pipecat frame processor that injects retrieved knowledge (ticket 4.06).

Sits between the user context aggregator and the LLM. On each ``LLMContextFrame``
it embeds the latest user utterance, retrieves the tenant's relevant chunks, and
rewrites the context with a refreshed KNOWLEDGE system block before the LLM runs.
Retrieval failures (OpenAI/Redis/DB) are swallowed so the call continues without
RAG rather than dropping.
"""

from __future__ import annotations

from uuid import UUID

import structlog
from pipecat.frames.frames import Frame, LLMContextFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

from app.services.knowledge_retrieval import DEFAULT_LIMIT, DEFAULT_THRESHOLD
from app.services.voice.rag import (
    RAGState,
    inject_knowledge,
    latest_user_query,
    retrieve_and_format,
)

logger = structlog.get_logger(__name__)


class RAGInjectionProcessor(FrameProcessor):
    def __init__(
        self,
        *,
        tenant_id: UUID,
        state: RAGState,
        threshold: float = DEFAULT_THRESHOLD,
        limit: int = DEFAULT_LIMIT,
    ) -> None:
        super().__init__()
        self._tenant_id = tenant_id
        self._state = state
        self._threshold = threshold
        self._limit = limit

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)

        if (
            isinstance(frame, LLMContextFrame)
            and direction == FrameDirection.DOWNSTREAM
        ):
            await self._maybe_inject(frame.context)

        await self.push_frame(frame, direction)

    async def _maybe_inject(self, context) -> None:
        try:
            query = latest_user_query(context.messages)
            if not query:
                return

            block, meta = await retrieve_and_format(
                self._tenant_id,
                query,
                threshold=self._threshold,
                limit=self._limit,
            )
            self._state.last_meta = meta

            if block is not None:
                context.set_messages(inject_knowledge(context.messages, block))
        except Exception as exc:  # never break the live call over RAG
            logger.warning("rag_injection_failed", error=str(exc))
