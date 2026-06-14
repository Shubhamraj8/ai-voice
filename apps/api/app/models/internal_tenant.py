from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.agent import Agent
from app.models.tenant import (
    ProviderConfig,
    Tenant,
    TenantMarket,
    TenantOnboardingMode,
    TenantStatus,
)


class TenantListItem(BaseModel):
    id: UUID
    slug: str
    business_name: str
    market: TenantMarket
    status: TenantStatus
    plan: str
    contact_email: str | None = None
    contact_phone: str | None = None
    agent_count: int = 0
    calls_last_7d: int = 0
    mrr_usd: float = 0.0
    created_at: datetime


class TenantListResponse(BaseModel):
    items: list[TenantListItem]
    total: int
    page: int
    page_size: int


class CallSummary(BaseModel):
    id: UUID
    twilio_call_sid: str
    from_number: str
    started_at: datetime
    ended_at: datetime | None = None
    duration_secs: int | None = None
    outcome: str | None = None


class CallVolumePoint(BaseModel):
    day: date
    count: int


class AuditLogEntry(BaseModel):
    id: UUID
    action: str
    actor_user_id: UUID | None = None
    payload: dict | None = None
    created_at: datetime


class TenantDetailResponse(BaseModel):
    tenant: Tenant
    agent_count: int = 0
    calls_last_7d: int = 0
    mrr_usd: float = 0.0
    agents: list[Agent] = Field(default_factory=list)
    recent_calls: list[CallSummary] = Field(default_factory=list)
    call_volume_14d: list[CallVolumePoint] = Field(default_factory=list)
    audit_log: list[AuditLogEntry] = Field(default_factory=list)
    audit_total: int = 0
    audit_page: int = 1
    audit_page_size: int = 25


class InternalTenantCreate(BaseModel):
    slug: str = Field(min_length=1, max_length=64)
    business_name: str = Field(min_length=1, max_length=200)
    market: TenantMarket = TenantMarket.INDIA_ENGLISH
    language: str = "en"
    timezone: str = "Asia/Kolkata"
    plan: str = "starter"
    onboarding_mode: TenantOnboardingMode = TenantOnboardingMode.SALES_LED
    status: TenantStatus = TenantStatus.ACTIVE
    contact_email: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    provider_config: ProviderConfig | None = None


class AvailableNumber(BaseModel):
    phone_number: str
    friendly_name: str | None = None
    locality: str | None = None
    region: str | None = None


class AvailableNumbersResponse(BaseModel):
    numbers: list[AvailableNumber] = Field(default_factory=list)


class TenantProvisionRequest(BaseModel):
    """Create a tenant and provision its first Twilio number in one flow (3.06)."""

    business_name: str = Field(min_length=1, max_length=200)
    phone_number: str = Field(min_length=1)  # chosen from the candidate list
    market: TenantMarket = TenantMarket.INDIA_ENGLISH
    region: str = "IN"
    contact_name: str | None = None
    contact_email: str | None = None


class InternalTenantPatch(BaseModel):
    business_name: str | None = Field(default=None, min_length=1, max_length=200)
    market: TenantMarket | None = None
    language: str | None = None
    timezone: str | None = None
    plan: str | None = None
    onboarding_mode: TenantOnboardingMode | None = None
    status: TenantStatus | None = None
    contact_email: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    provider_config: ProviderConfig | None = None
