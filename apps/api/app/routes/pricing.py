"""Public pricing endpoint (ticket 5.01) — powers the marketing pricing page."""

from fastapi import APIRouter

from app.models.pricing import PricingPlan
from app.services.pricing import list_pricing_plans

router = APIRouter(tags=["pricing"])


@router.get("/pricing-plans", response_model=list[PricingPlan])
async def get_pricing_plans() -> list[PricingPlan]:
    return await list_pricing_plans()
