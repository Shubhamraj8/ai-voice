"""Call recording capture and storage (ticket 2.14).

Approach A: when a call connects we start a Twilio recording with a
``recordingStatusCallback``. When Twilio reports the recording ready, the
recording webhook calls :func:`process_recording`, which downloads the MP3 and
uploads it to Supabase Storage at ``recordings/{tenant_id}/{call_id}.mp3``.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import httpx
import structlog

from app.config import get_settings
from app.services.calls import DEV_TENANT_ID, get_call_id_by_sid, set_recording_url
from app.services.storage import upload_recording

if TYPE_CHECKING:
    from app.config import Settings

logger = structlog.get_logger(__name__)

DOWNLOAD_MAX_RETRIES = 5
DOWNLOAD_BASE_DELAY_S = 1.0


def recording_status_callback_url(settings: Settings) -> str:
    base = settings.public_api_base_url.rstrip("/")
    return f"{base}{settings.twilio_recording_status_path}"


def start_call_recording(call_sid: str, settings: Settings) -> None:
    """Start a dual-channel Twilio recording for a live call (sync; runs in a
    background thread). Best-effort — failure never affects the call."""

    if not (settings.twilio_account_sid and settings.twilio_auth_token and call_sid):
        logger.info("recording_start_skipped", call_sid=call_sid)
        return

    try:
        from twilio.rest import Client

        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        client.calls(call_sid).recordings.create(
            recording_channels="dual",
            recording_status_callback=recording_status_callback_url(settings),
            recording_status_callback_event=["completed"],
        )
        logger.info("recording_started", call_sid=call_sid)
    except Exception as exc:
        logger.error("recording_start_failed", call_sid=call_sid, error=str(exc))


async def _download_twilio_recording(recording_url: str, settings: Settings) -> bytes:
    """Download a Twilio recording as MP3, retrying transient errors."""

    url = recording_url if recording_url.endswith(".mp3") else f"{recording_url}.mp3"
    auth = (settings.twilio_account_sid, settings.twilio_auth_token)
    last_exc: Exception | None = None

    for attempt in range(1, DOWNLOAD_MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(url, auth=auth)
                response.raise_for_status()
                return response.content
        except (httpx.HTTPStatusError, httpx.RequestError) as exc:
            last_exc = exc
            if attempt >= DOWNLOAD_MAX_RETRIES:
                break
            delay = DOWNLOAD_BASE_DELAY_S * (2 ** (attempt - 1))
            logger.warning(
                "recording_download_retry",
                attempt=attempt,
                delay_sec=delay,
                error=str(exc),
            )
            await asyncio.sleep(delay)

    assert last_exc is not None
    raise last_exc


async def process_recording(call_sid: str, recording_url: str) -> None:
    """Download a finished Twilio recording and store it in Supabase Storage.

    Best-effort end to end: any failure is logged, never raised, so the webhook
    that scheduled this job is unaffected.
    """

    settings = get_settings()
    try:
        call_id = await get_call_id_by_sid(call_sid)
        if call_id is None:
            logger.warning("recording_no_matching_call", call_sid=call_sid)
            return

        data = await _download_twilio_recording(recording_url, settings)

        object_path = f"{DEV_TENANT_ID}/{call_id}.mp3"
        if not await upload_recording(path=object_path, data=data):
            return

        storage_path = f"{settings.recordings_bucket}/{object_path}"
        await set_recording_url(twilio_call_sid=call_sid, path=storage_path)
        logger.info(
            "recording_stored",
            call_sid=call_sid,
            path=storage_path,
            bytes=len(data),
        )
    except Exception as exc:
        logger.error("recording_process_failed", call_sid=call_sid, error=str(exc))
