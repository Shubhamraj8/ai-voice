from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.db.pool import get_pool
from app.middleware.auth import InternalUserContext, require_internal_user
from app.models.internal_tenant import (
    InternalTenantCreate,
    InternalTenantPatch,
    TenantDetailResponse,
    TenantListResponse,
)
from app.models.tenant import Tenant, TenantMarket, TenantStatus
from app.services.audit import log_internal_action
from app.services.tenant_internal import (
    create_tenant,
    get_tenant_detail,
    list_tenants,
    patch_tenant,
)

router = APIRouter(prefix="/internal/tenants", tags=["internal-tenants"])


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
