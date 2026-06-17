"""Tool base class + execution context (ticket 4.07).

A ``Tool`` is the LLM-callable unit: a stable ``name``, a ``description`` the
model sees, a Pydantic ``parameters_schema`` (used both for the tool schema sent
to the LLM and to validate incoming arguments), and an async ``execute``. Tools
are pipecat-free so they can be unit-tested without the voice stack.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from pydantic import BaseModel


@dataclass
class ToolContext:
    """Per-call context handed to every tool's ``execute``."""

    tenant_id: UUID | None = None
    agent_id: UUID | None = None
    call_id: UUID | None = None  # DB calls.id
    twilio_call_sid: str | None = None  # live Twilio CallSid (call control)
    # Shared, session-scoped resources (db handles, clients, state). Reserved
    # for tools that need them; None unless the pipeline supplies it.
    resources: Any = None


class Tool(ABC):
    """Base class for an LLM-callable tool. Subclasses set the three class
    attributes and implement ``execute``."""

    name: str
    description: str
    parameters_schema: type[BaseModel]
    # Max successful invocations per call (None = unlimited). Enforced via Redis
    # in the dispatcher (ticket 4.12).
    max_per_call: int | None = None

    @abstractmethod
    async def execute(self, ctx: ToolContext, args: BaseModel) -> dict[str, Any]:
        """Run the tool. ``args`` is a validated ``parameters_schema`` instance.
        Return a JSON-serialisable dict surfaced back to the LLM."""
