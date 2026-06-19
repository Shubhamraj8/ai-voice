"""Billing ledger read models (ticket 5.07)."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

BillingEventType = Literal[
    "payment_recorded",
    "usage_reported",
    "access_extended",
    "plan_changed",
]


class BillingEvent(BaseModel):
    """One row of the billing/usage ledger, as returned by the read APIs.

    ``metadata`` holds offline references only (UPI/UTR ref, plan, period) — never
    payment-instrument data.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    call_id: UUID | None = None
    event_type: str
    units: float | None = None
    amount_inr: float | None = None
    metadata: dict | None = None
    created_at: datetime
