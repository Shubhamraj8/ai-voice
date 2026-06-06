"""Twilio voice and status webhook handlers (ticket 2.02)."""

import structlog
from fastapi import APIRouter, Request, Response

from app.config import get_settings
from app.webhooks.twilio_logging import STATUS_LOG_FIELDS, VOICE_LOG_FIELDS
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
async def twilio_voice_webhook(request: Request) -> Response:
    form = await request.form()
    params = {key: str(value) for key, value in form.multi_items()}
    validate_twilio_request(request, params)

    settings = get_settings()
    stream_url = build_media_stream_url(settings)
    twiml = build_voice_connect_twiml(stream_url)

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

    logger.info(
        "twilio_status_webhook",
        **log_fields(params, fields=STATUS_LOG_FIELDS),
    )
    return Response(status_code=204)
