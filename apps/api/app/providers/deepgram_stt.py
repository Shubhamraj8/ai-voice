"""Deepgram Nova-3 Monolingual STT provider — ticket 2.08.

Implements the STTProvider protocol via the Deepgram Listen WebSocket API
(deepgram-sdk v7+).  Audio is expected as 16-bit linear PCM at 16 kHz —
matching the Pipecat Twilio serializer output (``STT_INPUT_SAMPLE_RATE``).

Key features
------------
- Streaming via ``AsyncDeepgramClient.listen.v1.connect()`` WebSocket
- Model: ``nova-3``, language ``en``, ``smart_format=true``, ``endpointing=300``
- ``interim_results`` enabled — partial transcripts before finals
- ``vad_events`` enabled — speech-started / utterance-end for turn detection
- Reconnect on WebSocket close codes 1006 and 1011 (up to 3 attempts)
- Latency logging: audio-in → final transcript, and is_final receive → emit

Billing
-------
Nova-3 streaming PAYG: **$0.0048 / minute** (confirm on first dev-call invoice).
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager
from typing import Any

import structlog
from deepgram import AsyncDeepgramClient
from deepgram.listen.v1.types.listen_v1results import ListenV1Results
from deepgram.listen.v1.types.listen_v1speech_started import ListenV1SpeechStarted
from deepgram.listen.v1.types.listen_v1utterance_end import ListenV1UtteranceEnd
from websockets.exceptions import ConnectionClosed

from app.config import get_settings
from app.providers.base import Transcript

log = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MODEL = "nova-3"
_ENCODING = "linear16"
_SAMPLE_RATE = 16000  # matches app.services.voice.audio_config.STT_INPUT_SAMPLE_RATE
_ENDPOINTING_MS = 300
_LANGUAGE_DEFAULT = "en"

_RECONNECT_CLOSE_CODES = frozenset({1006, 1011})
_MAX_RECONNECTS = 3
_RECV_TIMEOUT_S = 0.25
_POST_FINALIZE_DRAIN_S = 2.0

# ---------------------------------------------------------------------------
# Internal exceptions
# ---------------------------------------------------------------------------


class _ReconnectableDisconnect(Exception):
    """WebSocket dropped mid-stream; caller should reconnect and resume."""

    def __init__(self, *, pending_audio: bytes | None = None) -> None:
        self.pending_audio = pending_audio
        super().__init__("WebSocket closed with a reconnectable code")


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------


class DeepgramSTT:
    """Deepgram Nova-3 streaming STT via the Listen WebSocket API (SDK v7).

    Satisfies the STTProvider protocol (app/providers/base.py).

    Usage::

        stt = DeepgramSTT()
        await stt.connect("en")
        async for transcript in stt.stream(audio_chunks):
            if transcript.is_final:
                handle_final(transcript.text)
        await stt.close()
    """

    _client_pool: dict[str, AsyncDeepgramClient] = {}

    def __init__(self) -> None:
        self._language = _LANGUAGE_DEFAULT
        self._client: AsyncDeepgramClient | None = None
        self._connect_cm: AbstractAsyncContextManager[Any] | None = None
        self._socket: Any | None = None
        self.connection: Any | None = None
        self._connected = False
        self._reconnect_count = 0
        self._first_audio_at: float | None = None
        self._utterance_started_at: float | None = None

    # ------------------------------------------------------------------
    # STTProvider protocol
    # ------------------------------------------------------------------

    async def connect(self, language: str) -> None:
        """Open the Deepgram Listen WebSocket for *language*."""
        if self._connected:
            return

        settings = get_settings()
        api_key = settings.deepgram_api_key
        if not api_key:
            raise RuntimeError(
                "DEEPGRAM_API_KEY is not set — cannot open STT stream. "
                "Set it in .env or Render environment variables."
            )

        self._language = _normalize_language(language)
        # Clear mock clients from pool in test environment to prevent contamination
        from unittest.mock import Mock

        if any(isinstance(c, Mock) for c in self._client_pool.values()):
            self._client_pool.clear()

        if api_key not in self._client_pool:
            self._client_pool[api_key] = AsyncDeepgramClient(api_key=api_key)
        self._client = self._client_pool[api_key]
        await self._open_socket()
        self._connected = True
        log.info(
            "deepgram_stt.connected",
            model=_MODEL,
            language=self._language,
            sample_rate=_SAMPLE_RATE,
            endpointing_ms=_ENDPOINTING_MS,
        )

    async def stream(
        self,
        audio_chunks: AsyncIterator[bytes],
    ) -> AsyncIterator[Transcript]:
        """Stream audio in and yield partial + final ``Transcript`` events."""
        try:
            if not self._connected or self._socket is None:
                raise RuntimeError(
                    "DeepgramSTT.connect() must be called before stream()"
                )

            chunk_iter = audio_chunks.__aiter__()
            resume_chunk: bytes | None = None
            self._reconnect_count = 0
            self._first_audio_at = None
            self._utterance_started_at = None

            while True:
                try:
                    async for transcript in self._stream_pass(
                        chunk_iter,
                        resume_chunk=resume_chunk,
                    ):
                        yield transcript
                    return
                except _ReconnectableDisconnect as exc:
                    self._reconnect_count += 1
                    if self._reconnect_count > _MAX_RECONNECTS:
                        raise RuntimeError(
                            f"DeepgramSTT: WebSocket reconnect failed after "
                            f"{_MAX_RECONNECTS} attempts."
                        ) from exc
                    resume_chunk = exc.pending_audio
                    log.warning(
                        "deepgram_stt.reconnect",
                        attempt=self._reconnect_count,
                        pending_bytes=len(resume_chunk) if resume_chunk else 0,
                    )
                    await self._reconnect()
        finally:
            if self.connection is not None:
                try:
                    if hasattr(self.connection, "close"):
                        if callable(self.connection.close):
                            await self.connection.close()
                    elif hasattr(self.connection, "send_close_stream"):
                        if callable(self.connection.send_close_stream):
                            await self.connection.send_close_stream()
                except Exception:  # noqa: BLE001
                    pass
                await self.close()

    async def close(self) -> None:
        """Tear down the Deepgram WebSocket connection."""
        await self._close_socket()
        self._connected = False
        self._client = None
        log.info("deepgram_stt.closed")

    # ------------------------------------------------------------------
    # Socket lifecycle
    # ------------------------------------------------------------------

    async def _open_socket(self) -> None:
        assert self._client is not None
        self._connect_cm = self._client.listen.v1.connect(
            model=_MODEL,
            language=self._language,
            encoding=_ENCODING,
            sample_rate=_SAMPLE_RATE,
            interim_results=True,
            smart_format=True,
            endpointing=_ENDPOINTING_MS,
            vad_events=True,
        )
        self._socket = await asyncio.wait_for(
            self._connect_cm.__aenter__(),
            timeout=30.0,
        )
        self.connection = self._socket

    async def _close_socket(self) -> None:
        if self.connection is not None:
            try:
                if hasattr(self.connection, "close"):
                    if callable(self.connection.close):
                        await self.connection.close()
                elif hasattr(self.connection, "send_close_stream"):
                    if callable(self.connection.send_close_stream):
                        await self.connection.send_close_stream()
            except Exception:  # noqa: BLE001
                pass
            self.connection = None
        if self._connect_cm is not None:
            await self._connect_cm.__aexit__(None, None, None)
            self._connect_cm = None

    async def _reconnect(self) -> None:
        await self._close_socket()
        await self._open_socket()

    # ------------------------------------------------------------------
    # Streaming pass (one connection lifetime)
    # ------------------------------------------------------------------

    async def _stream_pass(
        self,
        chunk_iter: AsyncIterator[bytes],
        *,
        resume_chunk: bytes | None,
    ) -> AsyncIterator[Transcript]:
        assert self._socket is not None
        socket = self._socket

        audio_queue: asyncio.Queue[bytes | None] = asyncio.Queue()
        send_exc: _ReconnectableDisconnect | None = None

        async def _feed_audio() -> None:
            nonlocal send_exc
            try:
                if resume_chunk:
                    await audio_queue.put(resume_chunk)
                async for chunk in chunk_iter:
                    await audio_queue.put(chunk)
                await audio_queue.put(None)
            except _ReconnectableDisconnect as exc:
                send_exc = exc
                await audio_queue.put(None)

        feeder_task = asyncio.create_task(_feed_audio())
        finalize_sent = False
        saw_final = False
        idle_deadline: float | None = None

        try:
            while True:
                print(
                    f"Loop start: finalize_sent={finalize_sent}, "
                    f"saw_final={saw_final}, send_exc={send_exc}"
                )
                if send_exc is not None:
                    raise send_exc

                while not finalize_sent:
                    try:
                        chunk = audio_queue.get_nowait()
                        print(
                            "Got chunk from queue: "
                            f"{None if chunk is None else len(chunk)} bytes"
                        )
                    except asyncio.QueueEmpty:
                        break
                    if chunk is None:
                        print("Sending finalize...")
                        await socket.send_finalize()
                        finalize_sent = True
                        break
                    await self._send_audio(chunk)

                if finalize_sent and idle_deadline is None:
                    idle_deadline = time.monotonic() + _POST_FINALIZE_DRAIN_S

                print(
                    f"Before check: finalize_sent={finalize_sent}, "
                    f"saw_final={saw_final}"
                )
                if finalize_sent and saw_final:
                    print("Breaking loop because finalize_sent and saw_final are True")
                    break

                try:
                    print("Awaiting socket.recv()...")
                    msg = await asyncio.wait_for(
                        socket.recv(),
                        timeout=_RECV_TIMEOUT_S,
                    )
                except TimeoutError:
                    if saw_final and finalize_sent:
                        break
                    if idle_deadline and time.monotonic() >= idle_deadline:
                        break
                    await asyncio.sleep(0.001)
                    continue
                except ConnectionClosed as exc:
                    if exc.code in _RECONNECT_CLOSE_CODES:
                        raise _ReconnectableDisconnect() from exc
                    raise

                transcript = self._parse_message(msg)
                if transcript is not None:
                    if transcript.is_final:
                        print("Setting saw_final = True")
                        saw_final = True
                    yield transcript
        finally:
            if not feeder_task.done():
                feeder_task.cancel()
            try:
                await feeder_task
            except (asyncio.CancelledError, _ReconnectableDisconnect):
                pass

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _send_audio(self, chunk: bytes) -> None:
        if self._first_audio_at is None:
            self._first_audio_at = time.monotonic()
        assert self._socket is not None
        try:
            await self._socket.send_media(chunk)
        except ConnectionClosed as exc:
            if exc.code in _RECONNECT_CLOSE_CODES:
                raise _ReconnectableDisconnect(pending_audio=chunk) from exc
            raise

    def _parse_message(self, msg: object) -> Transcript | None:
        if isinstance(msg, ListenV1SpeechStarted):
            self._utterance_started_at = time.monotonic()
            log.info("deepgram_stt.speech_started")
            return None

        if isinstance(msg, ListenV1UtteranceEnd):
            log.info("deepgram_stt.utterance_end")
            return None

        if not isinstance(msg, ListenV1Results):
            return None

        channel = msg.channel
        if not channel.alternatives:
            return None

        alternative = channel.alternatives[0]
        text = (alternative.transcript or "").strip()
        is_final = bool(msg.is_final)

        if not text and not is_final:
            return None

        t_received = time.monotonic()
        confidence = float(alternative.confidence or 0.0)
        transcript = Transcript(
            text=text,
            is_final=is_final,
            confidence=confidence,
            language=self._language,
        )
        t_emitted = time.monotonic()

        emit_latency_ms = round((t_emitted - t_received) * 1000)
        audio_to_final_ms: int | None = None
        if is_final and self._first_audio_at is not None:
            audio_to_final_ms = round((t_emitted - self._first_audio_at) * 1000)

        log.info(
            "deepgram_stt.transcript",
            text=text,
            is_final=is_final,
            confidence=confidence,
            emit_latency_ms=emit_latency_ms,
            audio_to_final_ms=audio_to_final_ms,
            speech_final=bool(msg.speech_final),
        )

        if is_final:
            self._utterance_started_at = None

        return transcript


def _normalize_language(language: str) -> str:
    """Map BCP-47 tags to Deepgram Nova-3 monolingual language codes."""
    if not language:
        return _LANGUAGE_DEFAULT
    base = language.split("-")[0].lower()
    return base if base else _LANGUAGE_DEFAULT
