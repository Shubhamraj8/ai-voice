"""Cross-tenant call history for internal staff (internal calls viewer)."""

from __future__ import annotations

from uuid import UUID

from app.db.pool import get_pool


async def list_all_calls(
    *,
    page: int = 1,
    page_size: int = 25,
    tenant_id: UUID | None = None,
    outcome: str | None = None,
) -> tuple[int, list[dict]]:
    """Return ``(total, rows)`` of recent calls across all tenants, newest first.

    Injection-safe: values are bound as params; only ``$N`` placeholders are
    interpolated into the dynamic WHERE clause.
    """

    conditions: list[str] = []
    params: list[object] = []

    def add(value: object) -> str:
        params.append(value)
        return f"${len(params)}"

    if tenant_id:
        conditions.append(f"c.tenant_id = {add(tenant_id)}")
    if outcome:
        conditions.append(f"c.outcome = {add(outcome)}")
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    pool = get_pool()
    async with pool.acquire() as conn:
        total = await conn.fetchval(f"SELECT COUNT(*) FROM calls c {where}", *params)
        limit_ph = add(page_size)
        offset_ph = add((page - 1) * page_size)
        rows = await conn.fetch(
            f"SELECT c.id, c.tenant_id, t.business_name AS tenant_name, "
            f"c.from_number, c.started_at, c.duration_secs, c.outcome, c.intent "
            f"FROM calls c JOIN tenants t ON t.id = c.tenant_id {where} "
            f"ORDER BY c.started_at DESC LIMIT {limit_ph} OFFSET {offset_ph}",
            *params,
        )

    return total or 0, [dict(row) for row in rows]
