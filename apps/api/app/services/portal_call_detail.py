"""Tenant-facing single-call detail (ticket 5.10).

Returns the transcript, tool dispatches, escalation, and a fresh 1-hour signed
recording URL for one call. Scoping is enforced in SQL (call must belong to the
tenant) as well as by RLS. Tool args/results are scrubbed of full phone numbers
before they reach the portal.
"""

from __future__ import annotations

import json
import re
from uuid import UUID

import structlog

from app.db.pool import get_pool
from app.models.portal import (
    CallDetail,
    CallEscalation,
    ToolDispatch,
    TranscriptMessage,
)
from app.services.storage import create_signed_url

logger = structlog.get_logger(__name__)

RECORDING_URL_TTL_S = 3600  # 1 hour, per ticket 5.10

# Keys (and value shapes) treated as phone numbers when scrubbing tool payloads.
_PHONE_KEYS = {
    "to",
    "from",
    "phone",
    "number",
    "recipient",
    "mobile",
    "caller",
    "to_number",
    "from_number",
}
_PHONE_VALUE = re.compile(r"^\+?[\d\s\-()]{10,20}$")


def _mask_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if len(digits) < 4:
        return value
    last4 = digits[-4:]
    cc_len = max(0, len(digits) - 10)
    cc = f"+{digits[:cc_len]} " if cc_len > 0 else ""
    return f"{cc}XXXXX X{last4}"


def _looks_like_phone(value: str) -> bool:
    if not _PHONE_VALUE.match(value.strip()):
        return False
    digits = re.sub(r"\D", "", value)
    return 10 <= len(digits) <= 15


def _scrub(value: object) -> object:
    """Recursively mask phone numbers in tool args/results for display."""

    if isinstance(value, dict):
        out: dict = {}
        for key, val in value.items():
            if isinstance(val, str) and (
                key.lower() in _PHONE_KEYS or _looks_like_phone(val)
            ):
                out[key] = _mask_phone(val)
            else:
                out[key] = _scrub(val)
        return out
    if isinstance(value, list):
        return [_scrub(item) for item in value]
    return value


def _load_json(raw: object) -> dict | None:
    if raw is None:
        return None
    if isinstance(raw, str):
        raw = json.loads(raw)
    return raw if isinstance(raw, dict) else {"value": raw}


async def get_call_detail(tenant_id: UUID, call_id: UUID) -> CallDetail | None:
    pool = get_pool()
    async with pool.acquire() as conn:
        call = await conn.fetchrow(
            """
            SELECT c.id, c.from_number, c.started_at, c.ended_at, c.duration_secs,
                   c.outcome, c.intent, c.summary, c.recording_url,
                   a.name AS agent_name
            FROM calls c
            LEFT JOIN agents a ON a.id = c.agent_id
            WHERE c.id = $1 AND c.tenant_id = $2
            """,
            call_id,
            tenant_id,
        )
        if call is None:
            return None

        messages = await conn.fetch(
            """
            SELECT role, content, tool_name, tool_args, tool_result,
                   latency_ms, created_at
            FROM call_messages
            WHERE call_id = $1
            ORDER BY created_at ASC, id ASC
            """,
            call_id,
        )
        escalation = await conn.fetchrow(
            """
            SELECT summary, urgency, created_at
            FROM escalations
            WHERE call_id = $1
            ORDER BY created_at DESC
            LIMIT 1
            """,
            call_id,
        )

    transcript: list[TranscriptMessage] = []
    tools: list[ToolDispatch] = []
    for msg in messages:
        if msg["tool_name"]:
            tools.append(
                ToolDispatch(
                    tool_name=msg["tool_name"],
                    tool_args=_scrub(_load_json(msg["tool_args"])),
                    tool_result=_scrub(_load_json(msg["tool_result"])),
                    created_at=msg["created_at"],
                )
            )
        elif msg["role"] in ("user", "assistant"):
            transcript.append(
                TranscriptMessage(
                    role=msg["role"],
                    content=msg["content"],
                    latency_ms=msg["latency_ms"],
                    created_at=msg["created_at"],
                )
            )

    recording_signed_url = None
    if call["recording_url"]:
        recording_signed_url = await create_signed_url(
            path=call["recording_url"], expires_in=RECORDING_URL_TTL_S
        )

    return CallDetail(
        id=call["id"],
        from_number=call["from_number"],
        started_at=call["started_at"],
        ended_at=call["ended_at"],
        duration_secs=call["duration_secs"],
        outcome=call["outcome"],
        intent=call["intent"],
        summary=call["summary"],
        agent_name=call["agent_name"],
        recording_signed_url=recording_signed_url,
        transcript=transcript,
        tools=tools,
        escalation=(
            CallEscalation(
                summary=escalation["summary"],
                urgency=escalation["urgency"],
                created_at=escalation["created_at"],
            )
            if escalation
            else None
        ),
    )
