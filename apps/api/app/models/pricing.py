from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PricingPlan(BaseModel):
    """A v1 pricing plan (ticket 5.01). Informational — no payment gateway."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    key: str
    name: str
    price_inr_month: int
    included_minutes: int
    overage_inr_per_min: float
    phone_numbers: int
    active: bool
    sort_order: int
