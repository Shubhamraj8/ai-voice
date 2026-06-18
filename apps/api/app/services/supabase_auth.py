"""Supabase Auth admin calls (ticket 5.04).

Invites a client login via the Supabase Auth admin REST API (service-role key).
The invite email carries a magic link for the user to set their password.
"""

from __future__ import annotations

import httpx
import structlog

from app.config import get_settings

logger = structlog.get_logger(__name__)


async def invite_user(email: str, *, metadata: dict | None = None) -> dict | None:
    """Invite a user by email; return the created user object, or None on failure."""

    settings = get_settings()
    base = settings.supabase_url.rstrip("/")
    headers = {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "Content-Type": "application/json",
    }
    body: dict = {"email": email}
    if metadata:
        body["data"] = metadata

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{base}/auth/v1/invite", json=body, headers=headers
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("supabase_invite_failed", email=email, error=str(exc))
        return None
