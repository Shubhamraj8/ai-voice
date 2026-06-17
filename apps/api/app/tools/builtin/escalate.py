"""escalateToOwner tool (ticket 4.10).

Notifies the tenant's owner (configured email and/or SMS) about a call that
needs attention, with a one-line summary and urgency. Fire-and-forget from the
agent's POV: it always reports success ("passed to the team") and records the
escalation for the audit trail — delivery failures never surface to the LLM.
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

import structlog
from pydantic import BaseModel, Field

from app.config import get_settings
from app.services.email import send_email
from app.services.escalations import get_escalation_config, log_escalation
from app.services.sms import get_agent_from_number, get_caller_number
from app.services.twilio_sms import send_sms
from app.tools.base import Tool, ToolContext
from app.tools.registry import registry

logger = structlog.get_logger(__name__)

URGENCY_PREFIX = {"high": "[URGENT]", "medium": "[HIGH]", "low": "[FYI]"}


class EscalateArgs(BaseModel):
    summary: str = Field(
        max_length=200, description="One-line summary of why this needs attention."
    )
    urgency: Literal["low", "medium", "high"] = "medium"


def _call_link(call_id: UUID | None) -> str:
    base = get_settings().public_app_base_url.rstrip("/")
    return f"{base}/calls/{call_id}" if call_id else base


def _build_email_html(
    *, business_name: str, call_id, caller: str | None, summary: str, urgency: str
) -> str:
    return (
        f"<h2>Call escalation — {business_name}</h2>"
        f"<p><strong>Urgency:</strong> {urgency}</p>"
        f"<p><strong>Summary:</strong> {summary}</p>"
        f"<p><strong>Caller:</strong> {caller or 'unknown'}</p>"
        f"<p><strong>Call ID:</strong> {call_id}</p>"
        f'<p><a href="{_call_link(call_id)}">View the call</a></p>'
    )


@registry.register
class EscalateToOwner(Tool):
    name = "escalateToOwner"
    description = (
        "Notify the business owner about a call that needs their attention, with "
        "a short summary and urgency. Use for complaints, urgent requests, or "
        "anything you cannot resolve."
    )
    parameters_schema = EscalateArgs
    max_per_call = 2

    async def execute(self, ctx: ToolContext, args: EscalateArgs) -> dict:
        config = await get_escalation_config(ctx.tenant_id) or {}
        business_name = config.get("business_name") or "your business"
        email_to = config.get("escalation_email")
        sms_to = config.get("escalation_sms")

        caller = await get_caller_number(ctx.call_id)
        prefix = URGENCY_PREFIX.get(args.urgency, "[FYI]")

        email_sent = False
        sms_sent = False
        error: str | None = None

        try:
            if email_to:
                email_sent = await send_email(
                    to=email_to,
                    subject=f"{prefix} Call escalation — {business_name}",
                    html=_build_email_html(
                        business_name=business_name,
                        call_id=ctx.call_id,
                        caller=caller,
                        summary=args.summary,
                        urgency=args.urgency,
                    ),
                )

            if sms_to:
                from_number = await get_agent_from_number(ctx.agent_id)
                if from_number:
                    await send_sms(
                        to=sms_to,
                        from_=from_number,
                        body=f"{prefix} {args.summary}",
                    )
                    sms_sent = True
        except Exception as exc:
            error = str(exc)
            logger.warning("escalation_send_failed", error=error)

        await log_escalation(
            tenant_id=ctx.tenant_id,
            call_id=ctx.call_id,
            summary=args.summary,
            urgency=args.urgency,
            email_sent=email_sent,
            sms_sent=sms_sent,
            payload={
                "summary": args.summary,
                "urgency": args.urgency,
                "caller": caller,
                "business_name": business_name,
                "email_to": email_to,
                "sms_to": sms_to,
                "call_link": _call_link(ctx.call_id),
            },
            error=error,
        )

        # Fire-and-forget: always succeed so the agent can say it was passed on.
        return {"status": "escalated"}
