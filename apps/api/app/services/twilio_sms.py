"""Twilio Messaging (ticket 4.09).

Sends SMS via the Twilio REST API. The SDK is synchronous, so sends run in a
worker thread. Built lazily so the app boots without Twilio credentials.
"""

from __future__ import annotations

import asyncio

import structlog

from app.config import get_settings

logger = structlog.get_logger(__name__)


def _client():
    from twilio.rest import Client

    settings = get_settings()
    return Client(settings.twilio_account_sid, settings.twilio_auth_token)


def sms_status_callback_url() -> str:
    base = get_settings().public_api_base_url.rstrip("/")
    return f"{base}/webhooks/twilio/sms-status"


async def send_sms(
    *, to: str, from_: str, body: str, status_callback: str | None = None
) -> tuple[str, str]:
    """Send an SMS; return ``(message_sid, status)``. Raises on Twilio error."""

    def _send():
        kwargs = {"to": to, "from_": from_, "body": body}
        if status_callback:
            kwargs["status_callback"] = status_callback
        message = _client().messages.create(**kwargs)
        return message.sid, message.status

    sid, status = await asyncio.to_thread(_send)
    logger.info("sms_sent", to=to, sid=sid, status=status)
    return sid, status
