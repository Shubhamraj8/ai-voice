"""Manual onboarding — provision a client login (ticket 5.04).

After the team provisions a tenant (3.06) and records payment (5.05), they invite
the client's portal login. The Supabase invite (5.04 option A) emails a magic
link; the new user is linked to the existing tenant via ``tenant_users`` (the
signup trigger skips auto-tenant creation for these provisioned users — migration
027). A welcome email points them at the portal.
"""

from __future__ import annotations

from uuid import UUID

import structlog

from app.config import get_settings
from app.db.pool import get_pool
from app.errors import api_error
from app.services.email import send_email
from app.services.supabase_auth import invite_user

logger = structlog.get_logger(__name__)


async def _send_welcome_email(email: str, business_name: str) -> None:
    base = get_settings().public_app_base_url.rstrip("/")
    html = (
        f"<h2>Welcome to ZERQO, {business_name}!</h2>"
        "<p>Your AI voice agent is set up. Check your inbox for an invite link to "
        "set your password, then sign in to your dashboard:</p>"
        f'<p><a href="{base}/login">{base}/login</a></p>'
    )
    await send_email(
        to=email, subject="Welcome to ZERQO — your dashboard is ready", html=html
    )


async def invite_tenant_login(
    tenant_id: UUID, email: str, *, role: str = "owner"
) -> dict:
    """Invite a portal login for an existing tenant and link it. Returns
    ``{user_id, email}``."""

    pool = get_pool()
    async with pool.acquire() as conn:
        tenant = await conn.fetchrow(
            "SELECT business_name FROM tenants WHERE id = $1", tenant_id
        )
    if tenant is None:
        raise api_error(404, "tenant_not_found", "Tenant not found")

    user = await invite_user(
        email, metadata={"provisioned": "true", "tenant_id": str(tenant_id)}
    )
    if not user or not user.get("id"):
        raise api_error(502, "invite_failed", "Could not invite the user")

    user_id = UUID(str(user["id"]))
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO tenant_users (tenant_id, user_id, role) "
            "VALUES ($1, $2, $3) ON CONFLICT DO NOTHING",
            tenant_id,
            user_id,
            role,
        )

    await _send_welcome_email(email, tenant["business_name"])
    logger.info("tenant_login_invited", tenant_id=str(tenant_id), email=email)
    return {"user_id": str(user_id), "email": email}
