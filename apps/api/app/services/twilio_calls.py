"""Live Twilio call control (ticket 4.08).

Uses the Twilio REST API to redirect an in-progress call. The Twilio SDK is
synchronous, so calls run in a worker thread. Built lazily so the app boots
without Twilio credentials.
"""

from __future__ import annotations

import asyncio
from xml.sax.saxutils import escape

import structlog

from app.config import get_settings

logger = structlog.get_logger(__name__)


def _client():
    from twilio.rest import Client

    settings = get_settings()
    return Client(settings.twilio_account_sid, settings.twilio_auth_token)


def _transfer_twiml(to_number: str, bridge_message: str) -> str:
    # Twilio speaks the bridge message, then dials the human — ordered and
    # reliable, no race with the media-stream teardown.
    return (
        "<Response>"
        f"<Say>{escape(bridge_message)}</Say>"
        f"<Dial>{escape(to_number)}</Dial>"
        "</Response>"
    )


class TwilioCallError(Exception):
    def __init__(self, message: str, code: str = "call_failed"):
        super().__init__(message)
        self.message = message
        self.code = code


async def place_outbound_call(
    *,
    to_number: str,
    from_number: str,
    voice_url: str,
    status_callback_url: str | None = None,
) -> str:
    """Place an outbound call from ``from_number`` to ``to_number``; Twilio fetches
    TwiML from ``voice_url`` (the same voice webhook + pipeline as inbound).
    Returns the Twilio CallSid on success, or raises TwilioCallError on failure.

    When ``status_callback_url`` is given, Twilio posts there on call completion
    so the call is closed with the real duration and the summary/cost jobs run
    (mirrors the inbound number's status callback). Without it an outbound call is
    only closed ~1h later by the stale-call reaper, yielding a bogus duration.
    """

    create_kwargs: dict[str, object] = {
        "to": to_number,
        "from_": from_number,
        "url": voice_url,
        "method": "POST",
    }
    if status_callback_url:
        create_kwargs["status_callback"] = status_callback_url
        create_kwargs["status_callback_event"] = ["completed"]
        create_kwargs["status_callback_method"] = "POST"

    try:
        call = await asyncio.to_thread(lambda: _client().calls.create(**create_kwargs))
        logger.info(
            "outbound_call_placed",
            to=to_number,
            from_=from_number,
            call_sid=call.sid,
        )
        return call.sid
    except Exception as exc:
        logger.error("outbound_call_failed", to=to_number, error=str(exc))
        msg = str(exc)
        code_attr = getattr(exc, "code", None)
        if code_attr in (21219, 21215) or "unverified" in msg.lower():
            friendly = (
                f"The phone number {to_number} is unverified. "
                "Your Twilio account is in Trial mode and can only "
                "call verified numbers. Please verify this number in "
                "your Twilio Console or upgrade your Twilio account."
            )
            raise TwilioCallError(friendly, code="twilio_unverified_number") from exc
        elif code_attr == 21211 or "not a valid phone number" in msg.lower():
            friendly = (
                f"Invalid phone number format ({to_number}). "
                "Please enter a valid number with country code in E.164 "
                "format (e.g. +9198XXXXXXXX)."
            )
            raise TwilioCallError(friendly, code="twilio_invalid_number") from exc
        elif code_attr == 21212:
            friendly = (
                f"Invalid caller ID ({from_number}). The agent's phone "
                "number is not owned by your Twilio account."
            )
            raise TwilioCallError(friendly, code="twilio_invalid_from_number") from exc
        elif code_attr == 21214 or "permission" in msg.lower():
            friendly = (
                "Twilio Geo-Permissions error: Outbound calling to this "
                "destination country is disabled in your Twilio Console."
            )
            raise TwilioCallError(friendly, code="twilio_geo_permission") from exc
        else:
            clean_msg = getattr(exc, "msg", msg)
            raise TwilioCallError(
                f"Twilio call failed: {clean_msg}", code="call_failed"
            ) from exc


async def transfer_call(call_sid: str, to_number: str, *, bridge_message: str) -> bool:
    """Redirect an in-progress call to ``to_number``. True on success."""

    twiml = _transfer_twiml(to_number, bridge_message)
    try:
        await asyncio.to_thread(lambda: _client().calls(call_sid).update(twiml=twiml))
        logger.info("call_transferred", call_sid=call_sid, to=to_number)
        return True
    except Exception as exc:
        logger.error("call_transfer_failed", call_sid=call_sid, error=str(exc))
        return False
