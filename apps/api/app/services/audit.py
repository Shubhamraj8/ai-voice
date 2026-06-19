"""Audit-log write helpers (tickets 1.13, generalized in 3.11).

One consistent shape for every internal-user and system write: actor, action,
optional target entity, tenant scope, and a redacted payload (the changed
fields — not full state). Writes are best-effort: a failure is logged, never
raised, so it can't break the request that triggered it.
"""

import json
import re
from uuid import UUID

import structlog

from app.db.pool import get_pool

logger = structlog.get_logger(__name__)

# Keys whose values are redacted before an audit payload is persisted (3.11).
_SENSITIVE_KEY_RE = re.compile(
    r"(token|secret|password|api[_-]?key|apikey|auth|payment|card|cvv)",
    re.IGNORECASE,
)
_REDACTED = "[REDACTED]"


def _redact(value):
    """Recursively redact sensitive values in an audit payload."""
    if isinstance(value, dict):
        return {
            key: (_REDACTED if _SENSITIVE_KEY_RE.search(key) else _redact(val))
            for key, val in value.items()
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


async def _write_audit(
    *,
    actor_user_id: UUID | None,
    actor_type: str,
    action: str,
    tenant_id: UUID | None,
    target_type: str | None,
    target_id: UUID | None,
    payload: dict | None,
) -> None:
    payload_json = json.dumps(_redact(payload)) if payload else None
    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO audit_log (
                    actor_user_id, actor_type, action,
                    target_type, target_id, payload, tenant_id
                )
                VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7)
                """,
                actor_user_id,
                actor_type,
                action,
                target_type,
                target_id,
                payload_json,
                tenant_id,
            )
    except Exception as exc:
        logger.error("audit_log_failed", error=str(exc), action=action)


async def log_internal_action(
    actor_id: UUID,
    action: str,
    *,
    tenant_id: UUID | None = None,
    target_type: str | None = None,
    target_id: UUID | None = None,
    payload: dict | None = None,
) -> None:
    """Write an audit row for an internal-user action (ticket 3.11)."""
    await _write_audit(
        actor_user_id=actor_id,
        actor_type="internal_user",
        action=action,
        tenant_id=tenant_id,
        target_type=target_type,
        target_id=target_id,
        payload=payload,
    )


async def log_tenant_action(
    actor_id: UUID,
    action: str,
    *,
    tenant_id: UUID,
    target_type: str | None = None,
    target_id: UUID | None = None,
    payload: dict | None = None,
) -> None:
    """Write an audit row for a tenant-user action (e.g. DPDP export, 5.12)."""
    await _write_audit(
        actor_user_id=actor_id,
        actor_type="tenant_user",
        action=action,
        tenant_id=tenant_id,
        target_type=target_type,
        target_id=target_id,
        payload=payload,
    )


async def log_system_action(
    action: str,
    *,
    tenant_id: UUID | None = None,
    target_type: str | None = None,
    target_id: UUID | None = None,
    payload: dict | None = None,
) -> None:
    """Write an audit row for a non-user-driven (system) action (ticket 3.11)."""
    await _write_audit(
        actor_user_id=None,
        actor_type="system",
        action=action,
        tenant_id=tenant_id,
        target_type=target_type,
        target_id=target_id,
        payload=payload,
    )
