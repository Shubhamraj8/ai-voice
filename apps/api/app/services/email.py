"""Transactional email via Resend (ticket 4.10).

Best-effort: when ``RESEND_API_KEY`` / ``ESCALATION_FROM_EMAIL`` are unset, or
the request fails, ``send_email`` returns False rather than raising, so callers
(escalations) degrade gracefully.
"""

from __future__ import annotations

import httpx
import structlog

from app.config import get_settings

logger = structlog.get_logger(__name__)

_RESEND_URL = "https://api.resend.com/emails"


async def send_email(*, to: str, subject: str, html: str) -> bool:
    """Send an HTML email. Returns True on success, False otherwise."""

    settings = get_settings()
    if not (settings.resend_api_key and settings.escalation_from_email):
        logger.warning("resend_not_configured")
        return False

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                _RESEND_URL,
                headers={"Authorization": f"Bearer {settings.resend_api_key}"},
                json={
                    "from": settings.escalation_from_email,
                    "to": [to],
                    "subject": subject,
                    "html": html,
                },
            )
            resp.raise_for_status()
        logger.info("email_sent", to=to, subject=subject)
        return True
    except Exception as exc:
        logger.error("email_send_failed", to=to, error=str(exc))
        return False
