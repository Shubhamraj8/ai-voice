"""DPDP data deletion (ticket 5.13).

Two-step erasure: a tenant requests deletion, we email a one-time confirmation
link, and only the click-through actually runs the (background) deletion. The
job soft-deletes the tenant (keeps the row so the audit trail survives), hard-
deletes messages + embeddings + Storage files, anonymizes caller numbers, clears
Twilio webhooks (the number is retained), and deletes the auth users so the
email can re-register into a brand-new tenant.
"""

from __future__ import annotations

import asyncio
import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import structlog

from app.config import get_settings
from app.db.pool import get_pool
from app.errors import api_error
from app.services.audit import log_system_action
from app.services.email import send_email
from app.services.storage import delete_document, delete_recording
from app.services.supabase_auth import delete_user
from app.services.twilio_numbers import clear_voice_webhook

logger = structlog.get_logger(__name__)

TOKEN_TTL_HOURS = 24

# Keep references to running tasks so they are not garbage-collected mid-flight.
_background_tasks: set[asyncio.Task] = set()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def request_deletion(
    tenant_id: UUID, *, requested_by: UUID, recipient_email: str | None
) -> dict:
    """Create a confirmation token and email the tenant a deletion link."""

    pool = get_pool()
    async with pool.acquire() as conn:
        tenant = await conn.fetchrow(
            "SELECT deletion_blocked, deleted_at FROM tenants WHERE id = $1",
            tenant_id,
        )
        if tenant is None:
            raise api_error(404, "tenant_not_found", "Tenant not found")
        if tenant["deleted_at"] is not None:
            raise api_error(409, "already_deleted", "This workspace is already deleted")
        if tenant["deletion_blocked"]:
            raise api_error(
                403,
                "deletion_blocked",
                "Deletion is disabled for this workspace. Please contact support.",
            )

        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(UTC) + timedelta(hours=TOKEN_TTL_HOURS)
        await conn.execute(
            """
            INSERT INTO dpdp_deletion_requests (
                tenant_id, token_hash, requested_by, recipient_email, expires_at
            )
            VALUES ($1, $2, $3, $4, $5)
            """,
            tenant_id,
            _hash_token(token),
            requested_by,
            recipient_email,
            expires_at,
        )

    if recipient_email:
        base = get_settings().public_app_base_url.rstrip("/")
        confirm_url = f"{base}/confirm-delete?token={token}"
        await send_email(
            to=recipient_email,
            subject="Confirm deletion of your ZERQO data",
            html=(
                "<h2>Confirm data deletion</h2>"
                "<p>You requested permanent deletion of your ZERQO workspace and "
                "all its data. This cannot be undone.</p>"
                f'<p><a href="{confirm_url}">Confirm and delete everything</a></p>'
                "<p>This link expires in 24 hours. If you didn&rsquo;t request "
                "this, you can safely ignore this email.</p>"
            ),
        )

    logger.info("dpdp_deletion_requested", tenant_id=str(tenant_id))
    return {"status": "confirmation_sent"}


async def confirm_deletion(token: str) -> dict:
    """Validate a confirmation token and schedule the deletion job."""

    token_hash = _hash_token(token)
    pool = get_pool()
    async with pool.acquire() as conn:
        req = await conn.fetchrow(
            """
            SELECT id, tenant_id, recipient_email, status, expires_at
            FROM dpdp_deletion_requests WHERE token_hash = $1
            """,
            token_hash,
        )
        if req is None:
            raise api_error(404, "invalid_token", "Invalid or unknown deletion link")
        if req["status"] != "pending":
            raise api_error(409, "already_used", "This deletion link was already used")
        if req["expires_at"] < datetime.now(UTC):
            raise api_error(410, "token_expired", "This deletion link has expired")

        await conn.execute(
            "UPDATE dpdp_deletion_requests "
            "SET status = 'confirmed', confirmed_at = now() WHERE id = $1",
            req["id"],
        )

    await log_system_action(
        "dpdp.deletion.confirmed",
        tenant_id=req["tenant_id"],
        target_type="tenant",
        target_id=req["tenant_id"],
    )
    schedule_deletion(
        req["tenant_id"], req["id"], recipient_email=req["recipient_email"]
    )
    return {"status": "confirmed"}


async def run_deletion(
    tenant_id: UUID, request_id: UUID, *, recipient_email: str | None = None
) -> None:
    """Execute the erasure. Best-effort + audited; the audit row survives."""

    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            recordings = await conn.fetch(
                "SELECT recording_url FROM calls "
                "WHERE tenant_id = $1 AND recording_url IS NOT NULL",
                tenant_id,
            )
            docs = await conn.fetch(
                "SELECT storage_path FROM knowledge_documents "
                "WHERE tenant_id = $1 AND storage_path IS NOT NULL",
                tenant_id,
            )
            sids = await conn.fetch(
                "SELECT DISTINCT twilio_sid FROM agents "
                "WHERE tenant_id = $1 AND twilio_sid IS NOT NULL",
                tenant_id,
            )
            users = await conn.fetch(
                "SELECT user_id FROM tenant_users WHERE tenant_id = $1", tenant_id
            )

        # External, best-effort deletes (Storage, Twilio, Auth).
        for row in recordings:
            await delete_recording(path=row["recording_url"])
        for row in docs:
            await delete_document(path=row["storage_path"])
        for row in sids:
            await clear_voice_webhook(row["twilio_sid"])
        for row in users:
            await delete_user(str(row["user_id"]))

        # Database changes atomically.
        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "DELETE FROM call_messages WHERE tenant_id = $1", tenant_id
                )
                await conn.execute(
                    "DELETE FROM knowledge_embeddings WHERE tenant_id = $1", tenant_id
                )
                # Anonymize residual caller numbers (the calls rows stay for stats).
                await conn.execute(
                    "UPDATE calls SET from_number = NULL WHERE tenant_id = $1",
                    tenant_id,
                )
                await conn.execute(
                    "UPDATE tenants SET deleted_at = now(), status = 'churned', "
                    "paid_until = NULL, archived_at = now(), updated_at = now() "
                    "WHERE id = $1",
                    tenant_id,
                )
                await conn.execute(
                    "DELETE FROM tenant_users WHERE tenant_id = $1", tenant_id
                )
                await conn.execute(
                    "UPDATE dpdp_deletion_requests "
                    "SET status = 'completed', completed_at = now() WHERE id = $1",
                    request_id,
                )

        await log_system_action(
            "dpdp.deletion.completed",
            tenant_id=tenant_id,
            target_type="tenant",
            target_id=tenant_id,
            payload={
                "recordings": len(recordings),
                "documents": len(docs),
                "users": len(users),
            },
        )

        if recipient_email:
            await send_email(
                to=recipient_email,
                subject="Your ZERQO data has been deleted",
                html=(
                    "<h2>Your data has been deleted</h2>"
                    "<p>Your ZERQO workspace and its data have been permanently "
                    "deleted. Thank you for using ZERQO.</p>"
                ),
            )
        logger.info("dpdp_deletion_completed", tenant_id=str(tenant_id))
    except Exception as exc:
        logger.error("dpdp_deletion_failed", tenant_id=str(tenant_id), error=str(exc))


def schedule_deletion(
    tenant_id: UUID, request_id: UUID, *, recipient_email: str | None = None
) -> None:
    """Run a deletion in the background, keeping a reference until it completes."""

    task = asyncio.create_task(
        run_deletion(tenant_id, request_id, recipient_email=recipient_email)
    )
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
