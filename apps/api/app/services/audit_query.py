"""Audit-log read/query for the internal viewer (ticket 3.12).

Paginated, newest-first listing with composable filters (actor type, action,
target type, tenant, date range, and a free-text search over actor email or
target id). Joins ``auth.users`` to surface the actor's email.
"""

from __future__ import annotations

import json
from datetime import datetime
from uuid import UUID

from app.models.internal_tenant import AuditLogListResponse, AuditLogRow


async def list_audit_log(
    conn,
    *,
    page: int,
    page_size: int,
    actor_type: str | None = None,
    action: str | None = None,
    target_type: str | None = None,
    tenant_id: UUID | None = None,
    search: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> AuditLogListResponse:
    where = ["TRUE"]
    params: list = []

    def _add(clause: str, value) -> None:
        params.append(value)
        where.append(clause.replace("$$", f"${len(params)}"))

    if actor_type:
        _add("al.actor_type = $$", actor_type)
    if action:
        _add("al.action ILIKE '%' || $$ || '%'", action)
    if target_type:
        _add("al.target_type = $$", target_type)
    if tenant_id:
        _add("al.tenant_id = $$", tenant_id)
    if date_from:
        _add("al.created_at >= $$", date_from)
    if date_to:
        _add("al.created_at <= $$", date_to)
    if search:
        params.append(search.strip())
        idx = len(params)
        where.append(
            f"(u.email ILIKE '%' || ${idx} || '%' "
            f"OR al.target_id::text ILIKE '%' || ${idx} || '%')"
        )

    where_sql = " AND ".join(where)

    count_row = await conn.fetchrow(
        f"""
        SELECT COUNT(*) AS total
        FROM audit_log al
        LEFT JOIN auth.users u ON u.id = al.actor_user_id
        WHERE {where_sql}
        """,
        *params,
    )
    total = count_row["total"] if count_row else 0

    offset = (page - 1) * page_size
    rows = await conn.fetch(
        f"""
        SELECT
          al.id, al.actor_user_id, u.email AS actor_email, al.actor_type,
          al.action, al.target_type, al.target_id, al.tenant_id,
          al.payload, al.created_at
        FROM audit_log al
        LEFT JOIN auth.users u ON u.id = al.actor_user_id
        WHERE {where_sql}
        ORDER BY al.created_at DESC
        LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}
        """,
        *params,
        page_size,
        offset,
    )

    items = []
    for row in rows:
        entry = dict(row)
        if isinstance(entry.get("payload"), str):
            entry["payload"] = json.loads(entry["payload"])
        items.append(AuditLogRow.model_validate(entry))

    return AuditLogListResponse(
        items=items, total=total, page=page, page_size=page_size
    )
