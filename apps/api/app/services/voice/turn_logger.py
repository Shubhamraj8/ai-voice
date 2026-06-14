"""Per-turn logging for the full voice pipeline (ticket 2.12)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from pipecat.frames.frames import MetricsFrame
from pipecat.metrics.metrics import (
    ProcessingMetricsData,
    TTSUsageMetricsData,
)
from pipecat.observers.base_observer import BaseObserver, FramePushed
from pipecat.observers.user_bot_latency_observer import (
    LatencyBreakdown,
    UserBotLatencyObserver,
)
from pipecat.processors.aggregators.llm_response_universal import (
    AssistantTurnStoppedMessage,
    LLMAssistantAggregator,
    LLMUserAggregator,
    UserTurnStoppedMessage,
)
from pipecat.processors.frame_processor import FrameDirection

from app.services.calls import record_turn
from app.services.voice.conversation_config import trim_conversation_history

if TYPE_CHECKING:
    from uuid import UUID

logger = structlog.get_logger(__name__)

# A turn slower than this end-to-end logs a warning for diagnosis (ticket 2.15).
SLOW_TURN_THRESHOLD_MS = 1500


def _ttfb_ms(breakdown: LatencyBreakdown, *, keyword: str) -> int | None:
    for metric in breakdown.ttfb:
        if keyword.lower() in metric.processor.lower():
            return round(metric.duration_secs * 1000)

    return None


def _processing_ms(metrics: list[object], *, keyword: str) -> int | None:
    for metric in metrics:
        if not isinstance(metric, ProcessingMetricsData):
            continue

        if keyword.lower() in metric.processor.lower():
            return round(metric.value * 1000)

    return None


class _TurnMetricsCollector(BaseObserver):
    """Collect TTS character usage from Pipecat usage metrics frames."""

    def __init__(self) -> None:
        super().__init__()
        self._last_tts_chars = 0
        self._pending_metrics: list[object] = []

    @property
    def last_tts_chars(self) -> int:
        return self._last_tts_chars

    def consume_pending_metrics(self) -> list[object]:
        metrics = self._pending_metrics

        self._pending_metrics = []

        return metrics

    async def on_push_frame(self, data: FramePushed) -> None:
        if data.direction != FrameDirection.DOWNSTREAM:
            return

        if not isinstance(data.frame, MetricsFrame):
            return

        self._pending_metrics.extend(data.frame.data)

        for metric in data.frame.data:
            if isinstance(metric, TTSUsageMetricsData):
                self._last_tts_chars = metric.value


def attach_turn_logging(
    *,
    user_aggregator: LLMUserAggregator,
    assistant_aggregator: LLMAssistantAggregator,
    latency_observer: UserBotLatencyObserver | None,
    metrics_collector: _TurnMetricsCollector,
    call_id: UUID | None = None,
    tenant_id: UUID | None = None,
) -> None:
    """Wire aggregator and latency events to structured per-turn logs.

    When ``call_id`` is provided (a persisted ``calls`` row exists), each turn
    is also written to ``call_messages`` for ticket 2.13. DB writes are
    best-effort and never interrupt the live call.
    """

    state: dict[str, object] = {
        "turn_number": 0,
        "user_input": "",
        "latency_ms": None,
        "breakdown": None,
    }

    @user_aggregator.event_handler("on_user_turn_stopped")
    async def on_user_turn_stopped(
        aggregator,
        strategy,
        message: UserTurnStoppedMessage,
    ) -> None:
        state["user_input"] = message.content

        trim_conversation_history(aggregator._context)

        logger.info(
            "conversation_user_turn",
            turn_number=state["turn_number"],
            user_input=message.content,
        )

        if call_id is not None:
            await record_turn(
                call_id=call_id,
                tenant_id=tenant_id,
                role="user",
                content=message.content,
            )

    @assistant_aggregator.event_handler("on_assistant_turn_stopped")
    async def on_assistant_turn_stopped(
        aggregator,
        message: AssistantTurnStoppedMessage,
    ) -> None:
        state["turn_number"] = int(state["turn_number"]) + 1

        breakdown: LatencyBreakdown | None = state.get("breakdown")  # type: ignore[assignment]

        pending_metrics = metrics_collector.consume_pending_metrics()

        stt_ms = _ttfb_ms(breakdown, keyword="STT") if breakdown else None

        llm_ms = _ttfb_ms(breakdown, keyword="LLM") or _processing_ms(
            pending_metrics, keyword="LLM"
        )

        tts_first_byte_ms = _ttfb_ms(breakdown, keyword="TTS") if breakdown else None

        total_ms = (
            round(float(state["latency_ms"]) * 1000)
            if state.get("latency_ms") is not None
            else None
        )

        tts_chars = metrics_collector.last_tts_chars or len(message.content)

        latency_breakdown = {
            "stt_ms": stt_ms,
            "llm_ms": llm_ms,
            "tts_first_byte_ms": tts_first_byte_ms,
            "total_ms": total_ms,
        }

        if total_ms is not None and total_ms > SLOW_TURN_THRESHOLD_MS:
            logger.warning(
                "slow_turn",
                turn_number=state["turn_number"],
                threshold_ms=SLOW_TURN_THRESHOLD_MS,
                **latency_breakdown,
            )

        logger.info(
            "conversation_turn_complete",
            turn_number=state["turn_number"],
            user_input=state["user_input"],
            assistant_output=message.content,
            interrupted=message.interrupted,
            stt_ms=stt_ms,
            llm_ms=llm_ms,
            tts_first_byte_ms=tts_first_byte_ms,
            total_ms=total_ms,
            tts_chars=tts_chars,
        )

        if call_id is not None:
            await record_turn(
                call_id=call_id,
                tenant_id=tenant_id,
                role="assistant",
                content=message.content,
                latency_ms=total_ms,
                tts_chars=tts_chars,
                latency_breakdown=latency_breakdown,
            )

        state["user_input"] = ""
        state["latency_ms"] = None
        state["breakdown"] = None

    if latency_observer is not None:

        @latency_observer.event_handler("on_latency_measured")
        async def on_latency_measured(observer, latency_seconds: float) -> None:
            state["latency_ms"] = latency_seconds

        @latency_observer.event_handler("on_latency_breakdown")
        async def on_latency_breakdown(observer, breakdown: LatencyBreakdown) -> None:
            state["breakdown"] = breakdown


def build_turn_metrics_collector() -> _TurnMetricsCollector:
    return _TurnMetricsCollector()
