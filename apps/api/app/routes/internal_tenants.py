from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from twilio.base.exceptions import TwilioRestException

from app.db.pool import get_pool
from app.errors import api_error
from app.middleware.auth import InternalUserContext, require_internal_user
from app.models.internal_tenant import (
    AvailableNumber,
    AvailableNumbersResponse,
    InternalTenantCreate,
    InternalTenantPatch,
    TenantDetailResponse,
    TenantListResponse,
    TenantProvisionRequest,
)
from app.models.tenant import Tenant, TenantMarket, TenantStatus
from app.services import twilio_numbers
from app.services.audit import log_internal_action
from app.services.tenant_internal import (
    create_default_agent,
    create_tenant,
    get_tenant_detail,
    list_tenants,
    patch_tenant,
    slugify,
)
from app.services.twilio_numbers import INDIA_LOCAL_MONTHLY_COST_USD

router = APIRouter(prefix="/internal/tenants", tags=["internal-tenants"])


def _twilio_error_message(exc: TwilioRestException) -> str:
    return getattr(exc, "msg", None) or str(exc)


@router.get("", response_model=TenantListResponse)
async def get_internal_tenants(
    _ctx: Annotated[InternalUserContext, Depends(require_internal_user)],
    pool=Depends(get_pool),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    status: TenantStatus | None = None,
    market: TenantMarket | None = None,
    search: str | None = None,
    has_active_calls: bool = False,
    sort: str = Query("-created_at"),
) -> TenantListResponse:
    async with pool.acquire() as conn:
        return await list_tenants(
            conn,
            page=page,
            page_size=page_size,
            status=status.value if status else None,
            market=market.value if market else None,
            search=search,
            has_active_calls=has_active_calls,
            sort=sort,
        )


@router.get("/available-numbers", response_model=AvailableNumbersResponse)
async def get_available_numbers(
    _ctx: Annotated[InternalUserContext, Depends(require_internal_user)],
    region: str = "IN",
    limit: int = Query(5, ge=1, le=10),
) -> AvailableNumbersResponse:
    try:
        found = await twilio_numbers.search_available_numbers(
            region=region, limit=limit
        )
    except TwilioRestException as exc:
        raise api_error(502, "twilio_search_failed", _twilio_error_message(exc))
    return AvailableNumbersResponse(numbers=[AvailableNumber(**n) for n in found])


@router.get("/{tenant_id}", response_model=TenantDetailResponse)
async def get_internal_tenant(
    tenant_id: UUID,
    _ctx: Annotated[InternalUserContext, Depends(require_internal_user)],
    pool=Depends(get_pool),
    audit_page: int = Query(1, ge=1),
    audit_page_size: int = Query(25, ge=1, le=100),
) -> TenantDetailResponse:
    async with pool.acquire() as conn:
        return await get_tenant_detail(
            conn,
            tenant_id,
            audit_page=audit_page,
            audit_page_size=audit_page_size,
        )


@router.post("", response_model=Tenant, status_code=201)
async def post_internal_tenant(
    body: InternalTenantCreate,
    ctx: Annotated[InternalUserContext, Depends(require_internal_user)],
    pool=Depends(get_pool),
) -> Tenant:
    async with pool.acquire() as conn:
        tenant = await create_tenant(conn, body)

    await log_internal_action(
        actor_id=ctx.user.id,
        action="internal.tenant.create",
        tenant_id=tenant.id,
        payload={
            "slug": tenant.slug,
            "business_name": tenant.business_name,
            "market": tenant.market.value,
        },
    )
    return tenant


@router.post("/provision", response_model=Tenant, status_code=201)
async def provision_tenant(
    body: TenantProvisionRequest,
    ctx: Annotated[InternalUserContext, Depends(require_internal_user)],
    pool=Depends(get_pool),
) -> Tenant:
    """Create a tenant + its first agent and provision a Twilio number (3.06)."""

    slug = slugify(body.business_name)

    # Fail fast on a slug collision before spending money on a number.
    async with pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT id FROM tenants WHERE slug = $1", slug)
    if existing:
        raise api_error(409, "slug_taken", f"A tenant '{slug}' already exists")

    # 1. Purchase the chosen number.
    try:
        number_sid = await twilio_numbers.purchase_number(body.phone_number)
    except TwilioRestException as exc:
        raise api_error(502, "twilio_purchase_failed", _twilio_error_message(exc))

    # 2. Configure its webhooks; release the number if this step fails.
    try:
        await twilio_numbers.configure_voice_webhook(number_sid)
    except TwilioRestException as exc:
        await twilio_numbers.release_number(number_sid)
        raise api_error(502, "twilio_configure_failed", _twilio_error_message(exc))

    # 3. Insert tenant + default agent atomically; release the number on failure.
    create_body = InternalTenantCreate(
        slug=slug,
        business_name=body.business_name,
        market=body.market,
        contact_name=body.contact_name,
        contact_email=body.contact_email,
    )
    try:
        async with pool.acquire() as conn:
            async with conn.transaction():
                tenant = await create_tenant(conn, create_body)
                agent = await create_default_agent(
                    conn,
                    tenant.id,
                    phone_number=body.phone_number,
                    twilio_sid=number_sid,
                )
    except Exception:
        await twilio_numbers.release_number(number_sid)
        raise

    # 4. Audit the create, the purchase (with cost), and the webhook config.
    await log_internal_action(
        actor_id=ctx.user.id,
        action="internal.tenant.create",
        tenant_id=tenant.id,
        payload={
            "slug": tenant.slug,
            "business_name": tenant.business_name,
            "market": tenant.market.value,
        },
    )
    await log_internal_action(
        actor_id=ctx.user.id,
        action="internal.tenant.purchase_number",
        tenant_id=tenant.id,
        payload={
            "phone_number": body.phone_number,
            "twilio_sid": number_sid,
            "monthly_cost_usd": INDIA_LOCAL_MONTHLY_COST_USD,
        },
    )
    await log_internal_action(
        actor_id=ctx.user.id,
        action="internal.tenant.configure_webhook",
        tenant_id=tenant.id,
        payload={"number_sid": number_sid, "agent_id": str(agent.id)},
    )

    return tenant


@router.patch("/{tenant_id}", response_model=Tenant)
async def patch_internal_tenant(
    tenant_id: UUID,
    body: InternalTenantPatch,
    ctx: Annotated[InternalUserContext, Depends(require_internal_user)],
    pool=Depends(get_pool),
) -> Tenant:
    async with pool.acquire() as conn:
        tenant = await patch_tenant(conn, tenant_id, body)

    await log_internal_action(
        actor_id=ctx.user.id,
        action="internal.tenant.update",
        tenant_id=tenant.id,
        payload=body.model_dump(exclude_unset=True, mode="json"),
    )
    return tenant
