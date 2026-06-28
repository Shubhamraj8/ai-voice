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


async def place_outbound_call(
    *, to_number: str, from_number: str, voice_url: str
) -> str | None:
    """Place an outbound call from ``from_number`` to ``to_number``; Twilio fetches
    TwiML from ``voice_url`` (the same voice webhook + pipeline as inbound).
    Returns the Twilio CallSid, or None on failure."""

    try:
        call = await asyncio.to_thread(
            lambda: _client().calls.create(
                to=to_number,
                from_=from_number,
                url=voice_url,
                method="POST",
            )
        )
        logger.info(
            "outbound_call_placed",
            to=to_number,
            from_=from_number,
            call_sid=call.sid,
        )
        return call.sid
    except Exception as exc:
        logger.error("outbound_call_failed", to=to_number, error=str(exc))
        return None


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
