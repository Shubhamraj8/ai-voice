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
