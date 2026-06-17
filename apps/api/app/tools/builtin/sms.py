"""sendSms tool (ticket 4.09).

Sends an SMS during a call from the agent's own Twilio number. Defaults the
recipient to the caller, truncates the body, logs to ``sms_log`` (delivery
status backfilled by the status webhook), and surfaces Twilio errors to the LLM.
"""

from __future__ import annotations

import structlog
from pydantic import BaseModel, Field

from app.services.sms import (
    get_agent_from_number,
    get_caller_number,
    log_sms,
    truncate_sms,
)
from app.services.twilio_sms import send_sms, sms_status_callback_url
from app.tools.base import Tool, ToolContext
from app.tools.registry import registry

logger = structlog.get_logger(__name__)


class SmsArgs(BaseModel):
    body: str = Field(description="The SMS text to send.")
    to: str | None = Field(
        default=None,
        description="Recipient in E.164 format. Defaults to the caller.",
    )


@registry.register
class SendSms(Tool):
    name = "sendSms"
    description = (
        "Send a text message (SMS) to the caller during the call, e.g. a link, "
        "address, or booking confirmation."
    )
    parameters_schema = SmsArgs
    max_per_call = 3

    async def execute(self, ctx: ToolContext, args: SmsArgs) -> dict:
        from_number = await get_agent_from_number(ctx.agent_id)
        if not from_number:
            return {"error": "no sending number is configured for this agent"}

        to_number = args.to or await get_caller_number(ctx.call_id)
        if not to_number:
            return {"error": "no recipient number is available"}

        body = truncate_sms(args.body)

        try:
            sid, status = await send_sms(
                to=to_number,
                from_=from_number,
                body=body,
                status_callback=sms_status_callback_url(),
            )
        except Exception as exc:
            logger.warning("send_sms_failed", error=str(exc))
            await log_sms(
                tenant_id=ctx.tenant_id,
                call_id=ctx.call_id,
                to_number=to_number,
                body=body,
                twilio_sid=None,
                status="failed",
                error=str(exc),
            )
            return {"error": "could not send the SMS"}

        await log_sms(
            tenant_id=ctx.tenant_id,
            call_id=ctx.call_id,
            to_number=to_number,
            body=body,
            twilio_sid=sid,
            status=status,
        )
        return {"status": status, "sid": sid, "to": to_number}
