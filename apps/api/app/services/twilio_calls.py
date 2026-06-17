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
