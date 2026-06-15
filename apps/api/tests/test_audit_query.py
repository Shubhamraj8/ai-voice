"""Unit tests for the audit-log query (ticket 3.12). DB mocked."""

import json
import uuid
from datetime import UTC, datetime

from app.services.audit_query import list_audit_log


async def test_list_audit_log_returns_rows(mock_db_pool):
    _pool, conn = mock_db_pool
    now = datetime.now(UTC)
    conn.fetchrow.return_value = {"total": 1}
    conn.fetch.return_value = [
        {
            "id": uuid.uuid4(),
            "actor_user_id": uuid.uuid4(),
            "actor_email": "admin@example.com",
            "actor_type": "internal_user",
            "action": "internal.agent.update",
            "target_type": "agent",
            "target_id": uuid.uuid4(),
            "tenant_id": uuid.uuid4(),
            "payload": json.dumps({"name": "New"}),
            "created_at": now,
        }
    ]

    result = await list_audit_log(conn, page=1, page_size=50)

    assert result.total == 1
    assert result.items[0].actor_email == "admin@example.com"
    assert result.items[0].payload == {"name": "New"}


async def test_list_audit_log_applies_filters(mock_db_pool):
    _pool, conn = mock_db_pool
    conn.fetchrow.return_value = {"total": 0}
    conn.fetch.return_value = []
    tenant = uuid.uuid4()

    await list_audit_log(
        conn,
        page=1,
        page_size=50,
        actor_type="system",
        tenant_id=tenant,
        search="admin@example.com",
    )

    # The filter values are passed as query params to the fetch.
    args = conn.fetch.await_args.args
    assert "system" in args
    assert tenant in args
    assert "admin@example.com" in args
