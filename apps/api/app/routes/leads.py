"""Public lead-capture endpoint (ticket 5.02) — landing-page CTAs post here."""

from fastapi import APIRouter, BackgroundTasks, Request

from app.errors import api_error
from app.models.leads import LeadCreate
from app.services import cache
from app.services.leads import create_lead, notify_team_of_lead

router = APIRouter(tags=["leads"])

LEAD_RATE_LIMIT = 5  # submissions per hour per IP
LEAD_RATE_TTL_S = 3600


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/leads", status_code=201)
async def submit_lead(
    body: LeadCreate,
    request: Request,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    # Best-effort per-IP rate limit (no-op when Redis is unavailable).
    count = await cache.incr_with_ttl(
        f"leadrl:{_client_ip(request)}", ttl_s=LEAD_RATE_TTL_S
    )
    if count is not None and count > LEAD_RATE_LIMIT:
        raise api_error(
            429, "rate_limited", "Too many requests. Please try again later."
        )

    lead = await create_lead(body)
    background_tasks.add_task(notify_team_of_lead, lead)
    return {"status": "received"}
