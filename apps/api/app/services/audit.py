import json
from uuid import UUID
import structlog

from app.db.pool import get_pool

logger = structlog.get_logger(__name__)

async def log_internal_action(
    actor_id: UUID,
    action: str,
    payload: dict | None = None,
    tenant_id: UUID | None = None,
):
    """
    Writes an audit log entry for an internal user action.
    """
    pool = get_pool()
    payload_json = json.dumps(payload) if payload else None
    
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO audit_log (actor_user_id, actor_type, action, payload, tenant_id)
                VALUES ($1, 'internal_user', $2, $3::jsonb, $4)
                """,
                actor_id,
                action,
                payload_json,
                tenant_id
            )
    except Exception as e:
        logger.error("audit_log_failed", error=str(e), action=action, actor_id=str(actor_id))
