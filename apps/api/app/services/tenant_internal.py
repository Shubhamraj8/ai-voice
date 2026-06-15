import json
import re
from uuid import UUID

from app.errors import api_error
from app.models.agent import Agent
from app.models.internal_tenant import (
    AuditLogEntry,
    CallSummary,
    CallVolumePoint,
    InternalTenantCreate,
    InternalTenantPatch,
    TenantDetailResponse,
    TenantListItem,
    TenantListResponse,
)
from app.models.tenant import Tenant, TenantStatus
from app.providers.registry import default_provider_config, validate_provider_config

# Default first-agent prompt (kept here, independent of the pipecat-importing
# conversation_config, so this service stays lightweight).
DEFAULT_AGENT_SYSTEM_PROMPT = (
    "You are a helpful AI receptionist for a business. "
    "Keep every reply under 25 words. Be warm, clear, and concise."
)

# Default voice for the first agent — a value from the Aura catalogue so the
# 3.08 voice dropdown shows it as a valid selection.
DEFAULT_AGENT_VOICE = "aura-asteria-en"


def slugify(value: str) -> str:
    """Lowercase, hyphenated, alphanumeric slug derived from a business name."""

    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "tenant"


def _parse_provider_config(value) -> dict:
    if isinstance(value, str):
        return json.loads(value)
    return value or {}


def _row_to_tenant(row) -> Tenant:
    row_dict = dict(row)
    row_dict["provider_config"] = _parse_provider_config(
        row_dict.get("provider_config")
    )
    return Tenant.model_validate(row_dict)


SORT_COLUMNS = {
    "created_at": "t.created_at",
    "-created_at": "t.created_at DESC",
    "calls_7d": "calls_last_7d",
    "-calls_7d": "calls_last_7d DESC",
    "mrr": "mrr_usd",
    "-mrr": "mrr_usd DESC",
}


async def list_tenants(
    conn,
    *,
    page: int,
    page_size: int,
    status: str | None,
    market: str | None,
    search: str | None,
    has_active_calls: bool,
    sort: str,
) -> TenantListResponse:
    order_clause = SORT_COLUMNS.get(sort, "t.created_at DESC")
    offset = (page - 1) * page_size

    where_clauses = ["TRUE"]
    params: list = []
    param_idx = 1

    if status:
        where_clauses.append(f"t.status = ${param_idx}")
        params.append(status)
        param_idx += 1

    if market:
        where_clauses.append(f"t.market = ${param_idx}")
        params.append(market)
        param_idx += 1

    if search:
        where_clauses.append(f"""(
                t.business_name ILIKE '%' || ${param_idx} || '%'
                OR coalesce(t.contact_email, '') ILIKE '%' || ${param_idx} || '%'
                OR coalesce(t.contact_phone, '') ILIKE '%' || ${param_idx} || '%'
                OR t.slug ILIKE '%' || ${param_idx} || '%'
            )""")
        params.append(search.strip())
        param_idx += 1

    if has_active_calls:
        where_clauses.append("""EXISTS (
                SELECT 1 FROM calls ac
                WHERE ac.tenant_id = t.id AND ac.ended_at IS NULL
            )""")

    where_sql = " AND ".join(where_clauses)

    count_row = await conn.fetchrow(
        f"SELECT COUNT(*) AS total FROM tenants t WHERE {where_sql}",
        *params,
    )
    total = count_row["total"] if count_row else 0

    rows = await conn.fetch(
        f"""
        SELECT
          t.id,
          t.slug,
          t.business_name,
          t.market,
          t.status,
          t.plan,
          t.contact_email,
          t.contact_phone,
          t.created_at,
          COUNT(DISTINCT a.id) FILTER (WHERE a.archived_at IS NULL) AS agent_count,
          COUNT(DISTINCT c.id) FILTER (
            WHERE c.started_at >= NOW() - INTERVAL '7 days'
          ) AS calls_last_7d,
          0::float AS mrr_usd
        FROM tenants t
        LEFT JOIN agents a ON a.tenant_id = t.id
        LEFT JOIN calls c ON c.tenant_id = t.id
        WHERE {where_sql}
        GROUP BY t.id
        ORDER BY {order_clause}
        LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """,
        *params,
        page_size,
        offset,
    )

    items = [TenantListItem.model_validate(dict(row)) for row in rows]
    return TenantListResponse(items=items, total=total, page=page, page_size=page_size)


async def get_tenant_detail(
    conn,
    tenant_id: UUID,
    *,
    audit_page: int,
    audit_page_size: int,
) -> TenantDetailResponse:
    row = await conn.fetchrow("SELECT * FROM tenants WHERE id = $1", tenant_id)
    if not row:
        raise api_error(404, "tenant_not_found", "Tenant not found")

    tenant = _row_to_tenant(row)

    stats = await conn.fetchrow(
        """
        SELECT
          COUNT(DISTINCT a.id) FILTER (WHERE a.archived_at IS NULL) AS agent_count,
          COUNT(DISTINCT c.id) FILTER (
            WHERE c.started_at >= NOW() - INTERVAL '7 days'
          ) AS calls_last_7d
        FROM tenants t
        LEFT JOIN agents a ON a.tenant_id = t.id
        LEFT JOIN calls c ON c.tenant_id = t.id
        WHERE t.id = $1
        GROUP BY t.id
        """,
        tenant_id,
    )

    agent_rows = await conn.fetch(
        """
        SELECT * FROM agents
        WHERE tenant_id = $1 AND archived_at IS NULL
        ORDER BY created_at DESC
        """,
        tenant_id,
    )
    agents = [Agent.model_validate(dict(r)) for r in agent_rows]

    call_rows = await conn.fetch(
        """
        SELECT id, twilio_call_sid, from_number, started_at, ended_at,
               duration_secs, outcome
        FROM calls
        WHERE tenant_id = $1
        ORDER BY started_at DESC
        LIMIT 5
        """,
        tenant_id,
    )
    recent_calls = [CallSummary.model_validate(dict(r)) for r in call_rows]

    volume_rows = await conn.fetch(
        """
        SELECT DATE(started_at) AS day, COUNT(*)::int AS count
        FROM calls
        WHERE tenant_id = $1
          AND started_at >= NOW() - INTERVAL '14 days'
        GROUP BY DATE(started_at)
        ORDER BY day
        """,
        tenant_id,
    )
    call_volume_14d = [
        CallVolumePoint(day=row["day"], count=row["count"]) for row in volume_rows
    ]

    audit_offset = (audit_page - 1) * audit_page_size
    audit_total_row = await conn.fetchrow(
        "SELECT COUNT(*) AS total FROM audit_log WHERE tenant_id = $1",
        tenant_id,
    )
    audit_total = audit_total_row["total"] if audit_total_row else 0

    audit_rows = await conn.fetch(
        """
        SELECT id, action, actor_user_id, payload, created_at
        FROM audit_log
        WHERE tenant_id = $1
        ORDER BY created_at DESC
        LIMIT $2 OFFSET $3
        """,
        tenant_id,
        audit_page_size,
        audit_offset,
    )
    audit_log = []
    for audit_row in audit_rows:
        entry = dict(audit_row)
        payload = entry.get("payload")
        if isinstance(payload, str):
            entry["payload"] = json.loads(payload)
        audit_log.append(AuditLogEntry.model_validate(entry))

    return TenantDetailResponse(
        tenant=tenant,
        agent_count=stats["agent_count"] if stats else 0,
        calls_last_7d=stats["calls_last_7d"] if stats else 0,
        mrr_usd=0.0,
        agents=agents,
        recent_calls=recent_calls,
        call_volume_14d=call_volume_14d,
        audit_log=audit_log,
        audit_total=audit_total,
        audit_page=audit_page,
        audit_page_size=audit_page_size,
    )


async def create_tenant(conn, body: InternalTenantCreate) -> Tenant:
    provider_config = body.provider_config or default_provider_config(body.market)
    validate_provider_config(provider_config)

    existing = await conn.fetchrow(
        "SELECT id FROM tenants WHERE slug = $1", body.slug.lower()
    )
    if existing:
        raise api_error(409, "slug_taken", "Tenant slug already exists")

    row = await conn.fetchrow(
        """
        INSERT INTO tenants (
          slug, business_name, market, language, timezone, plan,
          provider_config, onboarding_mode, status,
          contact_email, contact_name, contact_phone
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8, $9, $10, $11, $12)
        RETURNING *
        """,
        body.slug.lower(),
        body.business_name,
        body.market.value,
        body.language,
        body.timezone,
        body.plan,
        provider_config.model_dump_json(),
        body.onboarding_mode.value,
        body.status.value,
        body.contact_email,
        body.contact_name,
        body.contact_phone,
    )
    return _row_to_tenant(row)


async def create_default_agent(
    conn,
    tenant_id: UUID,
    *,
    phone_number: str,
    twilio_sid: str,
    voice_id: str | None = None,
) -> Agent:
    """Insert the tenant's first agent, holding the provisioned number (3.06)."""

    voice = voice_id or DEFAULT_AGENT_VOICE
    row = await conn.fetchrow(
        """
        INSERT INTO agents (
          tenant_id, name, starter_prompt, system_prompt, voice_id,
          phone_number, twilio_sid
        )
        VALUES ($1, $2, 'receptionist', $3, $4, $5, $6)
        RETURNING *
        """,
        tenant_id,
        "Main line",
        DEFAULT_AGENT_SYSTEM_PROMPT,
        voice,
        phone_number,
        twilio_sid,
    )
    return Agent.model_validate(dict(row))


async def patch_tenant(conn, tenant_id: UUID, body: InternalTenantPatch) -> Tenant:
    row = await conn.fetchrow("SELECT * FROM tenants WHERE id = $1", tenant_id)
    if not row:
        raise api_error(404, "tenant_not_found", "Tenant not found")

    updates: dict[str, object] = body.model_dump(exclude_unset=True)
    if not updates:
        return _row_to_tenant(row)

    if "provider_config" in updates and updates["provider_config"] is not None:
        validate_provider_config(updates["provider_config"])
        updates["provider_config"] = updates["provider_config"].model_dump_json()

    enum_fields = {
        "market": lambda v: v.value,
        "onboarding_mode": lambda v: v.value,
        "status": lambda v: v.value,
    }
    for field, to_value in enum_fields.items():
        if field in updates and updates[field] is not None:
            updates[field] = to_value(updates[field])

    set_parts = []
    params: list = []
    for key, value in updates.items():
        param_idx = len(params) + 1
        if key == "provider_config":
            set_parts.append(f"provider_config = ${param_idx}::jsonb")
        else:
            set_parts.append(f"{key} = ${param_idx}")
        params.append(value)

    if updates.get("status") == TenantStatus.CHURNED.value:
        set_parts.append("archived_at = NOW()")
    elif updates.get("status") in (
        TenantStatus.ACTIVE.value,
        TenantStatus.PAUSED.value,
    ):
        set_parts.append("archived_at = NULL")

    set_parts.append("updated_at = NOW()")
    params.append(tenant_id)
    where_param = len(params)

    updated = await conn.fetchrow(
        f"""
        UPDATE tenants
        SET {", ".join(set_parts)}
        WHERE id = ${where_param}
        RETURNING *
        """,
        *params,
    )
    return _row_to_tenant(updated)
