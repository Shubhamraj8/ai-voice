"""Agent CRUD for the internal dashboard (ticket 3.07).

Tenant-scoped create / list / update / soft-delete with voice-id validation
against the Aura voice catalogue. Soft delete sets ``archived_at`` so the agent
stops answering calls while historical call rows stay intact.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException

from app.errors import api_error
from app.models.agent import Agent, AgentCreate, AgentPatch
from app.providers.deepgram_tts import VOICE_CATALOGUE


def validate_voice_id(voice_id: str) -> None:
    if voice_id not in VOICE_CATALOGUE:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "invalid_voice_id",
                "message": f"Unknown voice_id '{voice_id}'.",
                "allowed": VOICE_CATALOGUE,
            },
        )


def _row_to_agent(row) -> Agent:
    return Agent.model_validate(dict(row))


async def _get_agent_scoped(conn, tenant_id: UUID, agent_id: UUID):
    """Fetch an agent and enforce it belongs to ``tenant_id`` (else 403/404)."""

    row = await conn.fetchrow("SELECT * FROM agents WHERE id = $1", agent_id)
    if not row:
        raise api_error(404, "agent_not_found", "Agent not found")
    if row["tenant_id"] != tenant_id:
        raise api_error(403, "cross_tenant", "Agent belongs to another tenant")
    return row


async def list_agents(conn, tenant_id: UUID) -> list[Agent]:
    rows = await conn.fetch(
        """
        SELECT * FROM agents
        WHERE tenant_id = $1 AND archived_at IS NULL
        ORDER BY created_at DESC
        """,
        tenant_id,
    )
    return [_row_to_agent(r) for r in rows]


async def create_agent(conn, tenant_id: UUID, body: AgentCreate) -> Agent:
    validate_voice_id(body.voice_id)

    existing = await conn.fetchrow(
        "SELECT id FROM agents WHERE phone_number = $1", body.phone_number
    )
    if existing:
        raise api_error(
            409, "phone_number_taken", "That phone number is already assigned"
        )

    row = await conn.fetchrow(
        """
        INSERT INTO agents (
          tenant_id, name, starter_prompt, system_prompt, tools,
          voice_id, phone_number, twilio_sid
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING *
        """,
        tenant_id,
        body.name,
        body.starter_prompt.value,
        body.system_prompt,
        body.tools,
        body.voice_id,
        body.phone_number,
        body.twilio_sid,
    )
    return _row_to_agent(row)


async def patch_agent(conn, tenant_id: UUID, agent_id: UUID, body: AgentPatch) -> Agent:
    await _get_agent_scoped(conn, tenant_id, agent_id)

    updates = body.model_dump(exclude_unset=True)
    if not updates:
        row = await conn.fetchrow("SELECT * FROM agents WHERE id = $1", agent_id)
        return _row_to_agent(row)

    if updates.get("voice_id") is not None:
        validate_voice_id(updates["voice_id"])

    set_parts: list[str] = []
    params: list = []
    for key, value in updates.items():
        params.append(value)
        set_parts.append(f"{key} = ${len(params)}")
    set_parts.append("updated_at = NOW()")
    params.append(agent_id)

    row = await conn.fetchrow(
        f"UPDATE agents SET {', '.join(set_parts)} WHERE id = ${len(params)} "
        "RETURNING *",
        *params,
    )
    return _row_to_agent(row)


async def soft_delete_agent(conn, tenant_id: UUID, agent_id: UUID) -> Agent:
    await _get_agent_scoped(conn, tenant_id, agent_id)

    row = await conn.fetchrow(
        """
        UPDATE agents
        SET archived_at = NOW(), is_active = false, updated_at = NOW()
        WHERE id = $1
        RETURNING *
        """,
        agent_id,
    )
    return _row_to_agent(row)
