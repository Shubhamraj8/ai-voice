"""Tenant-facing call history queries (ticket 5.09).

A paginated, filterable list of the caller's own calls. User-supplied values are
always passed as query parameters; only ``$N`` placeholders are interpolated into
the SQL, so the dynamic WHERE clause is injection-safe.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from uuid import UUID

import structlog

from app.db.pool import get_pool
from app.models.portal import CallListPage, RecentCall

logger = structlog.get_logger(__name__)

MAX_INTENT_OPTIONS = 20


async def list_tenant_calls(
    tenant_id: UUID,
    *,
    page: int = 1,
    page_size: int = 25,
    outcome: str | None = None,
    intent: str | None = None,
    search: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> CallListPage:
    conditions = ["tenant_id = $1"]
    params: list[object] = [tenant_id]

    def add(value: object) -> str:
        params.append(value)
        return f"${len(params)}"

    if outcome:
        conditions.append(f"outcome = {add(outcome)}")
    if intent:
        conditions.append(f"intent = {add(intent)}")
    if date_from:
        conditions.append(f"started_at >= {add(date_from)}")
    if date_to:
        conditions.append(f"started_at <= {add(date_to)}")
    if search:
        like = add(f"%{search}%")
        conditions.append(f"(from_number ILIKE {like} OR summary ILIKE {like})")

    where = " AND ".join(conditions)
    offset = (page - 1) * page_size

    # Prepare limit and offset params for rows query
    rows_params = list(params)
    limit_ph = f"${len(rows_params) + 1}"
    offset_ph = f"${len(rows_params) + 2}"
    rows_params.extend([page_size, offset])

    pool = get_pool()
    async with pool.acquire() as conn:
        total, rows, intent_rows = await asyncio.gather(
            conn.fetchval(f"SELECT COUNT(*) FROM calls WHERE {where}", *params),
            conn.fetch(
                f"SELECT id, from_number, started_at, duration_secs, "
                f"outcome, intent, summary "
                f"FROM calls WHERE {where} "
                f"ORDER BY started_at DESC LIMIT {limit_ph} OFFSET {offset_ph}",
                *rows_params,
            ),
            conn.fetch(
                "SELECT DISTINCT intent FROM calls "
                "WHERE tenant_id = $1 AND intent IS NOT NULL "
                "ORDER BY intent LIMIT $2",
                tenant_id,
                MAX_INTENT_OPTIONS,
            ),
        )

    return CallListPage(
        items=[RecentCall(**dict(row)) for row in rows],
        total=total or 0,
        page=page,
        page_size=page_size,
        available_intents=[row["intent"] for row in intent_rows],
    )
