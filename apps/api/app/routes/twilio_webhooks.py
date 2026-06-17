"""Twilio voice and status webhook handlers (ticket 2.02)."""

import structlog
from fastapi import APIRouter, BackgroundTasks, Request, Response

from app.config import get_settings
from app.services.call_routing import resolve_agent_by_number
from app.services.calls import end_call, start_call
from app.services.recording import process_recording, start_call_recording
from app.services.sms import update_sms_status
from app.services.voice import agent_registry
from app.webhooks.twilio_logging import (
    RECORDING_LOG_FIELDS,
    STATUS_LOG_FIELDS,
    VOICE_LOG_FIELDS,
)
from app.webhooks.twilio_logging import twilio_payload_for_log as log_fields
from app.webhooks.twilio_signature import validate_twilio_request
from app.webhooks.twilio_twiml import (
    build_media_stream_url,
    build_not_configured_twiml,
    build_voice_connect_twiml,
)

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

    # Resolve the dialed number to its tenant + agent (ticket 3.09).
    to_number = params.get("To", "")
    route = await resolve_agent_by_number(to_number)

    if route is None:
        logger.info(
            "twilio_voice_unconfigured",
            to_number=to_number,
            **log_fields(params, fields=VOICE_LOG_FIELDS),
        )
        return Response(
            content=build_not_configured_twiml(), media_type="application/xml"
        )

    stream_url = build_media_stream_url(settings)
    twiml = build_voice_connect_twiml(stream_url)

    call_sid = params.get("CallSid", "")
    if call_sid:
        await start_call(
            twilio_call_sid=call_sid,
            from_number=params.get("From", ""),
            provider_snapshot={
                "stt": route.stt,
                "tts": route.tts,
                "llm": route.llm,
            },
            tenant_id=route.tenant_id,
            agent_id=route.agent_id,
        )
        # Start the Twilio recording out-of-band so the webhook stays fast.
        background_tasks.add_task(start_call_recording, call_sid, settings)

    logger.info(
        "twilio_voice_webhook",
        stream_url=stream_url,
        resolved_tenant_id=str(route.tenant_id),
        resolved_agent_id=str(route.agent_id),
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
            # Force agent cleanup in case the websocket lingers (ticket 2.18).
            await agent_registry.terminate(call_sid)

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


@router.post(
    "/sms-status",
    summary="Twilio SMS status callback",
    description=(
        "Validates the Twilio signature and backfills the delivery status of a "
        "sent SMS onto its sms_log row (ticket 4.09)."
    ),
    status_code=204,
)
async def twilio_sms_status_webhook(request: Request) -> Response:
    form = await request.form()
    params = {key: str(value) for key, value in form.multi_items()}
    validate_twilio_request(request, params)

    message_sid = params.get("MessageSid") or params.get("SmsSid") or ""
    message_status = params.get("MessageStatus") or params.get("SmsStatus") or ""
    error_code = params.get("ErrorCode") or None
    if message_sid and message_status:
        await update_sms_status(message_sid, message_status, error=error_code)

    logger.info(
        "twilio_sms_status_webhook",
        message_sid=message_sid,
        message_status=message_status,
        error_code=error_code,
    )
    return Response(status_code=204)
