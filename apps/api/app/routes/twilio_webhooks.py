"""Twilio voice and status webhook handlers (ticket 2.02)."""

import structlog
from fastapi import APIRouter, BackgroundTasks, Request, Response

from app.config import get_settings
from app.services.calls import build_provider_snapshot, end_call, start_call
from app.services.recording import process_recording, start_call_recording
from app.webhooks.twilio_logging import (
    RECORDING_LOG_FIELDS,
    STATUS_LOG_FIELDS,
    VOICE_LOG_FIELDS,
)
from app.webhooks.twilio_logging import twilio_payload_for_log as log_fields
from app.webhooks.twilio_signature import validate_twilio_request
from app.webhooks.twilio_twiml import build_media_stream_url, build_voice_connect_twiml

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/webhooks/twilio", tags=["twilio-webhooks"])


@router.post(
    "/voice",
    summary="Twilio inbound voice webhook",
    description=(
        "Validates the Twilio signature and returns TwiML that opens a "
        "Media Streams websocket (tenant lookup added in ticket 3.09)."
    ),
)
async def twilio_voice_webhook(
    request: Request, background_tasks: BackgroundTasks
) -> Response:
    form = await request.form()
    params = {key: str(value) for key, value in form.multi_items()}
    validate_twilio_request(request, params)

    settings = get_settings()
    stream_url = build_media_stream_url(settings)
    twiml = build_voice_connect_twiml(stream_url)

    call_sid = params.get("CallSid", "")
    if call_sid:
        await start_call(
            twilio_call_sid=call_sid,
            from_number=params.get("From", ""),
            provider_snapshot=build_provider_snapshot(settings),
        )
        # Start the Twilio recording out-of-band so the webhook stays fast.
        background_tasks.add_task(start_call_recording, call_sid, settings)

    logger.info(
        "twilio_voice_webhook",
        stream_url=stream_url,
        **log_fields(params, fields=VOICE_LOG_FIELDS),
    )
    return Response(content=twiml, media_type="application/xml")


@router.post(
    "/status",
    summary="Twilio call status callback",
    description="Validates the Twilio signature and logs call lifecycle events.",
    status_code=204,
)
async def twilio_status_webhook(request: Request) -> Response:
    form = await request.form()
    params = {key: str(value) for key, value in form.multi_items()}
    validate_twilio_request(request, params)

    if params.get("CallStatus") == "completed":
        call_sid = params.get("CallSid", "")
        raw_duration = params.get("CallDuration", "")
        if call_sid:
            await end_call(
                twilio_call_sid=call_sid,
                duration_secs=int(raw_duration) if raw_duration.isdigit() else None,
            )

    logger.info(
        "twilio_status_webhook",
        **log_fields(params, fields=STATUS_LOG_FIELDS),
    )
    return Response(status_code=204)


@router.post(
    "/recording",
    summary="Twilio recording status callback",
    description=(
        "Validates the Twilio signature and, when the recording is ready, "
        "schedules its download and upload to Supabase Storage (ticket 2.14)."
    ),
    status_code=204,
)
async def twilio_recording_webhook(
    request: Request, background_tasks: BackgroundTasks
) -> Response:
    form = await request.form()
    params = {key: str(value) for key, value in form.multi_items()}
    validate_twilio_request(request, params)

    if params.get("RecordingStatus") == "completed":
        call_sid = params.get("CallSid", "")
        recording_url = params.get("RecordingUrl", "")
        if call_sid and recording_url:
            background_tasks.add_task(process_recording, call_sid, recording_url)

    logger.info(
        "twilio_recording_webhook",
        **log_fields(params, fields=RECORDING_LOG_FIELDS),
    )
    return Response(status_code=204)
