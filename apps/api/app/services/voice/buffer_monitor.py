"""Monitor outbound audio for buffer gaps that may cause glitches (ticket 2.05)."""

from __future__ import annotations

import time

import structlog
from pipecat.frames.frames import AudioRawFrame, Frame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

logger = structlog.get_logger(__name__)

UNDERRUN_GAP_MULTIPLIER = 2.5


class AudioBufferUnderrunMonitor(FrameProcessor):
    """Log when gaps between outbound audio frames exceed expected playout time."""

    def __init__(self, *, gap_multiplier: float = UNDERRUN_GAP_MULTIPLIER) -> None:
        super().__init__()
        self._gap_multiplier = gap_multiplier
        self._last_frame_monotonic: float | None = None
        self._underrun_count = 0

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)

        if (
            direction == FrameDirection.DOWNSTREAM
            and isinstance(frame, AudioRawFrame)
            and frame.audio
            and frame.sample_rate > 0
        ):
            now = time.monotonic()
            sample_count = len(frame.audio) // 2
            expected_duration = sample_count / frame.sample_rate

            if self._last_frame_monotonic is not None and expected_duration > 0:
                gap = now - self._last_frame_monotonic
                threshold = expected_duration * self._gap_multiplier
                if gap > threshold:
                    self._underrun_count += 1
                    logger.warning(
                        "audio_buffer_underrun",
                        gap_ms=round(gap * 1000, 1),
                        expected_ms=round(expected_duration * 1000, 1),
                        sample_rate=frame.sample_rate,
                        underrun_count=self._underrun_count,
                    )

            self._last_frame_monotonic = now

        await self.push_frame(frame, direction)
