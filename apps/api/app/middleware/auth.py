import json
import time
from typing import Annotated, Any
from uuid import UUID

import httpx
import jwt
import structlog
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.config import Settings, get_settings
from app.db.pool import get_pool
from app.errors import api_error
from app.models.tenant import Tenant
from app.models.user import TenantUserRole


class User(BaseModel):
    id: UUID
    email: str | None = None
    role: str | None = None


class TenantContext(BaseModel):
    tenant: Tenant
    role: TenantUserRole


class InternalUserContext(BaseModel):
    user: User
    internal_role: str


logger = structlog.get_logger(__name__)
security = HTTPBearer(auto_error=False)

JWKS_CACHE: dict[str, Any] = {"keys": {}, "expires_at": 0}
JWKS_CACHE_TTL = 600  # 10 minutes


async def fetch_jwks(supabase_url: str) -> dict:
    jwks_url = f"{supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
    async with httpx.AsyncClient() as client:
        response = await client.get(jwks_url)
        response.raise_for_status()
        return response.json()


async def get_jwks() -> dict:
    settings = get_settings()
    current_time = time.time()

    if current_time > JWKS_CACHE["expires_at"]:
        logger.info("jwks_cache_miss", action="fetch_jwks")
        try:
            jwks = await fetch_jwks(settings.supabase_url)
            keys = {key["kid"]: key for key in jwks.get("keys", [])}
            JWKS_CACHE["keys"] = keys
            JWKS_CACHE["expires_at"] = current_time + JWKS_CACHE_TTL
        except Exception as e:
            logger.error("jwks_fetch_failed", error=str(e))
            if not JWKS_CACHE["keys"]:
                raise api_error(500, "jwks_unavailable", "Failed to fetch JWKS")

    return JWKS_CACHE["keys"]


def _public_key_and_algorithms(key_data: dict) -> tuple[Any, list[str]]:
    kty = key_data.get("kty")
    if kty == "RSA":
        return jwt.algorithms.RSAAlgorithm.from_jwk(key_data), ["RS256"]
    if kty == "EC":
        return jwt.algorithms.ECAlgorithm.from_jwk(key_data), ["ES256"]
    raise api_error(401, "invalid_token", "Unsupported signing key")


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> User:
    if not credentials:
        raise api_error(401, "missing_token", "Missing token")
    token = credentials.credentials
    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        if not kid:
            raise api_error(401, "invalid_token", "Invalid token: missing kid")

        jwks = await get_jwks()
        key_data = jwks.get(kid)
        if not key_data:
            raise api_error(401, "invalid_token", "Invalid token: unknown kid")

        public_key, algorithms = _public_key_and_algorithms(key_data)

        decoded = jwt.decode(
            token,
            public_key,
            algorithms=algorithms,
            audience="authenticated",
            leeway=10,
        )

        user_id_str = decoded.get("sub")
        if not user_id_str:
            raise api_error(401, "invalid_token", "Invalid token: missing subject")

        return User(
            id=UUID(user_id_str),
            email=decoded.get("email"),
            role=decoded.get("role"),
        )

    except jwt.ExpiredSignatureError:
        raise api_error(401, "token_expired", "Token has expired")
    except jwt.InvalidTokenError:
        raise api_error(401, "invalid_token", "Invalid token")
    except jwt.PyJWTError:
        raise api_error(401, "invalid_token", "Invalid token")


async def get_current_tenant(
    user: Annotated[User, Depends(get_current_user)],
    pool=Depends(get_pool),
) -> TenantContext:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT t.*, tu.role as tu_role FROM tenants t
            JOIN tenant_users tu ON t.id = tu.tenant_id
            WHERE tu.user_id = $1
            LIMIT 1
            """,
            user.id,
        )
        if not row:
            raise api_error(403, "no_tenant", "User does not belong to any tenant")

        row_dict = dict(row)
        if isinstance(row_dict.get("provider_config"), str):
            row_dict["provider_config"] = json.loads(row_dict["provider_config"])

        return TenantContext(
            tenant=Tenant.model_validate(row_dict),
            role=TenantUserRole(row_dict["tu_role"]),
        )


async def _try_promote_founding_internal_user(
    conn,
    user: User,
    settings: Settings,
) -> None:
    """Auto-promote the founding internal user on first authenticated request."""
    if not settings.internal_user_email or not user.email:
        return

    if user.email.lower() != settings.internal_user_email.lower():
        return

    await conn.execute(
        """
        INSERT INTO internal_users (user_id, role)
        VALUES ($1, 'admin')
        ON CONFLICT (user_id) DO NOTHING
        """,
        user.id,
    )


async def require_internal_user(
    user: Annotated[User, Depends(get_current_user)],
    pool=Depends(get_pool),
) -> InternalUserContext:
    settings = get_settings()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT role FROM internal_users
            WHERE user_id = $1
            """,
            user.id,
        )
        if not row:
            await _try_promote_founding_internal_user(conn, user, settings)
            row = await conn.fetchrow(
                """
                SELECT role FROM internal_users
                WHERE user_id = $1
                """,
                user.id,
            )
        if not row:
            raise api_error(403, "not_internal", "User does not have internal access")

        return InternalUserContext(user=user, internal_role=row["role"])


def require_internal_role(role: str):
    """Dependency factory — e.g. Depends(require_internal_role('admin'))."""

    async def _require(
        ctx: Annotated[InternalUserContext, Depends(require_internal_user)],
    ) -> InternalUserContext:
        if ctx.internal_role != role:
            raise api_error(
                403,
                "insufficient_internal_role",
                f"Requires internal role: {role}",
            )
        return ctx

    return _require
