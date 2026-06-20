"""Twilio phone-number provisioning (ticket 3.06).

Thin async wrappers over the (synchronous) Twilio REST SDK for searching,
purchasing, configuring, and releasing numbers. The SDK calls run in a thread
so they don't block the event loop.
"""

from __future__ import annotations

import asyncio

import structlog

from app.config import get_settings

logger = structlog.get_logger(__name__)

# Twilio India local number list rental (used for audit/cost surfacing).
INDIA_LOCAL_MONTHLY_COST_USD = 1.15


def _client():
    from twilio.rest import Client

    settings = get_settings()
    return Client(settings.twilio_account_sid, settings.twilio_auth_token)


def _voice_webhook_url() -> str:
    base = get_settings().public_api_base_url.rstrip("/")
    return f"{base}/webhooks/twilio/voice"


def _status_callback_url() -> str:
    base = get_settings().public_api_base_url.rstrip("/")
    return f"{base}/webhooks/twilio/status"


async def search_available_numbers(
    *, region: str, limit: int = 5
) -> list[dict[str, str | None]]:
    """Return up to ``limit`` purchasable local numbers in ``region``."""

    def _search() -> list[dict[str, str | None]]:
        numbers = _client().available_phone_numbers(region).local.list(limit=limit)
        return [
            {
                "phone_number": n.phone_number,
                "friendly_name": n.friendly_name,
                "locality": getattr(n, "locality", None),
                "region": getattr(n, "region", None),
            }
            for n in numbers
        ]

    return await asyncio.to_thread(_search)


async def purchase_number(phone_number: str) -> str:
    """Buy ``phone_number``; return its IncomingPhoneNumber SID."""

    def _purchase() -> str:
        incoming = _client().incoming_phone_numbers.create(phone_number=phone_number)
        return incoming.sid

    sid = await asyncio.to_thread(_purchase)
    logger.info("twilio_number_purchased", phone_number=phone_number, number_sid=sid)
    return sid


async def configure_voice_webhook(number_sid: str) -> None:
    """Point a purchased number's voice + status webhooks at this service."""

    voice_url = _voice_webhook_url()
    status_url = _status_callback_url()

    def _configure() -> None:
        _client().incoming_phone_numbers(number_sid).update(
            voice_url=voice_url,
            voice_method="POST",
            status_callback=status_url,
            status_callback_method="POST",
        )

    await asyncio.to_thread(_configure)
    logger.info("twilio_number_configured", number_sid=number_sid, voice_url=voice_url)


async def release_number(number_sid: str) -> None:
    """Release a purchased number (compensating action on provisioning failure)."""

    def _release() -> None:
        _client().incoming_phone_numbers(number_sid).delete()

    try:
        await asyncio.to_thread(_release)
        logger.info("twilio_number_released", number_sid=number_sid)
    except Exception as exc:
        # Best-effort cleanup — log, never mask the original error.
        logger.error(
            "twilio_number_release_failed", number_sid=number_sid, error=str(exc)
        )


async def clear_voice_webhook(number_sid: str) -> None:
    """Detach our webhooks from a number on tenant deletion (5.13). The number is
    retained (not released); a deleted tenant's calls simply stop reaching us.
    Best-effort: failures are logged, never raised."""

    def _clear() -> None:
        _client().incoming_phone_numbers(number_sid).update(
            voice_url="", status_callback=""
        )

    try:
        await asyncio.to_thread(_clear)
        logger.info("twilio_voice_webhook_cleared", number_sid=number_sid)
    except Exception as exc:
        logger.error(
            "twilio_voice_webhook_clear_failed", number_sid=number_sid, error=str(exc)
        )
