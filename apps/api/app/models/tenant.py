from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TenantMarket(StrEnum):
    INDIA_ENGLISH = "india_english"
    INDIA_HINDI = "india_hindi"
    US_ENGLISH = "us_english"
    US_HIPAA = "us_hipaa"
    GLOBAL_ENGLISH = "global_english"


class TenantOnboardingMode(StrEnum):
    SALES_LED = "sales_led"
    SELF_SERVE = "self_serve"
    HYBRID = "hybrid"


class TenantStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    CHURNED = "churned"


class ProviderConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stt: str
    tts: str
    llm: str


class Tenant(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    business_name: str
    market: TenantMarket
    language: str
    timezone: str
    plan: str
    provider_config: ProviderConfig
    onboarding_mode: TenantOnboardingMode
    status: TenantStatus = TenantStatus.ACTIVE
    contact_email: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    paid_until: datetime | None = None
    archived_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def india_english_defaults(cls) -> dict[str, object]:
        return {
            "market": TenantMarket.INDIA_ENGLISH,
            "language": "en",
            "timezone": "Asia/Kolkata",
            "plan": "starter",
            "provider_config": ProviderConfig(
                stt="cartesia",
                tts="inworld",
                llm="deepseek_native",
            ),
            "onboarding_mode": TenantOnboardingMode.SELF_SERVE,
        }


class TenantCreate(BaseModel):
    slug: str = Field(min_length=1)
    business_name: str = Field(min_length=1)
    market: TenantMarket = TenantMarket.INDIA_ENGLISH
    language: str = "en"
    timezone: str = "Asia/Kolkata"
    plan: str = "starter"
    provider_config: ProviderConfig = Field(
        default_factory=lambda: ProviderConfig(
            stt="cartesia",
            tts="inworld",
            llm="deepseek_native",
        )
    )
    onboarding_mode: TenantOnboardingMode = TenantOnboardingMode.SELF_SERVE
