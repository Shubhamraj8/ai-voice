from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.db.pool import get_pool
from app.middleware.auth import InternalUserContext, require_internal_user
from app.models.agent import Agent, AgentCreate, AgentPatch
from app.services.agent_internal import (
    create_agent,
    list_agents,
    patch_agent,
    soft_delete_agent,
)
from app.services.audit import log_internal_action

router = APIRouter(
    prefix="/internal/tenants/{tenant_id}/agents", tags=["internal-agents"]
)


@router.get("", response_model=list[Agent])
async def get_agents(
    tenant_id: UUID,
    _ctx: Annotated[InternalUserContext, Depends(require_internal_user)],
    pool=Depends(get_pool),
) -> list[Agent]:
    async with pool.acquire() as conn:
        return await list_agents(conn, tenant_id)


@router.post("", response_model=Agent, status_code=201)
async def post_agent(
    tenant_id: UUID,
    body: AgentCreate,
    ctx: Annotated[InternalUserContext, Depends(require_internal_user)],
    pool=Depends(get_pool),
) -> Agent:
    async with pool.acquire() as conn:
        agent = await create_agent(conn, tenant_id, body)

    await log_internal_action(
        actor_id=ctx.user.id,
        action="internal.agent.create",
        tenant_id=tenant_id,
        payload={
            "agent_id": str(agent.id),
            "name": agent.name,
            "phone_number": agent.phone_number,
        },
    )
    return agent


@router.patch("/{agent_id}", response_model=Agent)
async def patch_agent_route(
    tenant_id: UUID,
    agent_id: UUID,
    body: AgentPatch,
    ctx: Annotated[InternalUserContext, Depends(require_internal_user)],
    pool=Depends(get_pool),
) -> Agent:
    async with pool.acquire() as conn:
        agent = await patch_agent(conn, tenant_id, agent_id, body)

    await log_internal_action(
        actor_id=ctx.user.id,
        action="internal.agent.update",
        tenant_id=tenant_id,
        payload={
            "agent_id": str(agent_id),
            **body.model_dump(exclude_unset=True, mode="json"),
        },
    )
    return agent


@router.delete("/{agent_id}", response_model=Agent)
async def delete_agent_route(
    tenant_id: UUID,
    agent_id: UUID,
    ctx: Annotated[InternalUserContext, Depends(require_internal_user)],
    pool=Depends(get_pool),
) -> Agent:
    async with pool.acquire() as conn:
        agent = await soft_delete_agent(conn, tenant_id, agent_id)

    await log_internal_action(
        actor_id=ctx.user.id,
        action="internal.agent.delete",
        tenant_id=tenant_id,
        payload={"agent_id": str(agent_id)},
    )
    return agent
