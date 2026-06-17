"""transferToHuman tool (ticket 4.08).

Transfers the live call to the human number configured on the agent
(``agents.transfer_to_number``). Twilio speaks a short bridge message, then
dials the human. Missing/unconfigured number returns an error the LLM can
apologise for.
"""

from __future__ import annotations

from uuid import UUID

import structlog
from pydantic import BaseModel, Field

from app.db.pool import get_pool
from app.services.calls import set_call_outcome
from app.services.twilio_calls import transfer_call
from app.tools.base import Tool, ToolContext
from app.tools.registry import registry

logger = structlog.get_logger(__name__)

BRIDGE_MESSAGE = "Connecting you to a team member, one moment."


class TransferArgs(BaseModel):
    reason: str | None = Field(
        default=None, description="Why the call is being transferred."
    )


async def _agent_transfer_number(agent_id: UUID | None) -> str | None:
    if agent_id is None:
        return None
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT transfer_to_number FROM agents WHERE id = $1", agent_id
        )
    return row["transfer_to_number"] if row else None


@registry.register
class TransferToHuman(Tool):
    name = "transferToHuman"
    description = (
        "Transfer the current call to a human team member. Use when the caller "
        "asks to speak to a person or when you cannot help them."
    )
    parameters_schema = TransferArgs

    async def execute(self, ctx: ToolContext, args: TransferArgs) -> dict:
        if not ctx.twilio_call_sid:
            return {"error": "there is no active call to transfer"}

        number = await _agent_transfer_number(ctx.agent_id)
        if not number:
            return {"error": "no transfer number is configured for this agent"}

        ok = await transfer_call(
            ctx.twilio_call_sid, number, bridge_message=BRIDGE_MESSAGE
        )
        if not ok:
            return {"error": "could not transfer the call right now"}

        if ctx.call_id is not None:
            await set_call_outcome(ctx.call_id, "transferred")

        logger.info("transfer_to_human", reason=args.reason)
        return {"status": "transferring", "to": number}
