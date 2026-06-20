"""Portal dashboard read models (ticket 5.08)."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class DashboardStats(BaseModel):
    calls_this_month: int
    minutes_used: float
    minutes_included: int
    escalations_this_month: int


class CallPoint(BaseModel):
    """One day in the 14-day calls-over-time series."""

    date: date
    count: int


class RecentCall(BaseModel):
    id: UUID
    from_number: str
    started_at: datetime
    duration_secs: int | None = None
    outcome: str | None = None
    intent: str | None = None
    summary: str | None = None


class KnowledgeStatus(BaseModel):
    document_count: int
    ready_count: int
    last_upload: datetime | None = None


class PlanCard(BaseModel):
    key: str
    name: str | None = None
    included_minutes: int
    paid_until: datetime | None = None


class DashboardSummary(BaseModel):
    stats: DashboardStats
    calls_over_time: list[CallPoint]
    recent_calls: list[RecentCall]
    knowledge: KnowledgeStatus
    plan: PlanCard


class CallListPage(BaseModel):
    """A page of the tenant's call history (ticket 5.09)."""

    items: list[RecentCall]
    total: int
    page: int
    page_size: int
    available_intents: list[str]


class ConsentDisclosure(BaseModel):
    """The disclosure spoken before recording on a tenant's calls (ticket 5.14)."""

    text: str
    is_custom: bool
    default_text: str


class BillingUsage(BaseModel):
    cycle_start: date
    cycle_end: date
    minutes_used: float
    included_minutes: int
    overage_minutes: float
    projected_minutes: float


class BillingAccess(BaseModel):
    paid_until: datetime | None = None
    status: str
    days_remaining: int | None = None
    # none | active | expiring_soon | expired
    expiry_state: str


class BillingSummary(BaseModel):
    """Read-only billing overview for the portal (ticket 5.11)."""

    plan: PlanCard
    usage: BillingUsage
    access: BillingAccess


class TranscriptMessage(BaseModel):
    role: str
    content: str
    created_at: datetime
    latency_ms: int | None = None


class ToolDispatch(BaseModel):
    tool_name: str
    tool_args: dict | None = None
    tool_result: dict | None = None
    created_at: datetime


class CallEscalation(BaseModel):
    summary: str
    urgency: str
    created_at: datetime


class CallDetail(BaseModel):
    """Full per-call view for the portal (ticket 5.10)."""

    id: UUID
    from_number: str
    started_at: datetime
    ended_at: datetime | None = None
    duration_secs: int | None = None
    outcome: str | None = None
    intent: str | None = None
    summary: str | None = None
    agent_name: str | None = None
    recording_signed_url: str | None = None
    transcript: list[TranscriptMessage]
    tools: list[ToolDispatch]
    escalation: CallEscalation | None = None
