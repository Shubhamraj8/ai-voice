import json
import time
from typing import Annotated, Any
from uuid import UUID

import httpx
import jwt
import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from pydantic import BaseModel

from app.config import get_settings
from app.db.pool import get_pool
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
            # Store keys by kid for easy lookup
            keys = {key["kid"]: key for key in jwks.get("keys", [])}
            JWKS_CACHE["keys"] = keys
            JWKS_CACHE["expires_at"] = current_time + JWKS_CACHE_TTL
        except Exception as e:
            logger.error("jwks_fetch_failed", error=str(e))
            if not JWKS_CACHE["keys"]:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch JWKS",
                )
    
    return JWKS_CACHE["keys"]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)]
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing token",
        )
    token = credentials.credentials
    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing kid",
            )

        jwks = await get_jwks()
        key_data = jwks.get(kid)
        if not key_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: unknown kid",
            )
            
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key_data)
        
        decoded = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience="authenticated",
        )
        
        user_id_str = decoded.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject",
            )
            
        return User(
            id=UUID(user_id_str),
            email=decoded.get("email"),
            role=decoded.get("role"),
        )
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


async def get_current_tenant(
    user: Annotated[User, Depends(get_current_user)],
    pool=Depends(get_pool),
) -> TenantContext:
    async with pool.acquire() as conn:
        # Load the first tenant this user has access to
        row = await conn.fetchrow(
            """
            SELECT t.*, tu.role as tu_role FROM tenants t
            JOIN tenant_users tu ON t.id = tu.tenant_id
            WHERE tu.user_id = $1
            LIMIT 1
            """,
            user.id
        )
        if not row:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not belong to any tenant",
            )
        
        row_dict = dict(row)
        if isinstance(row_dict.get("provider_config"), str):
            row_dict["provider_config"] = json.loads(row_dict["provider_config"])
            
        return TenantContext(
            tenant=Tenant.model_validate(row_dict),
            role=row_dict["tu_role"]
        )


async def require_internal_user(
    user: Annotated[User, Depends(get_current_user)],
    pool=Depends(get_pool),
) -> InternalUserContext:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT role FROM internal_users
            WHERE user_id = $1
            """,
            user.id
        )
        if not row:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have internal access",
            )
            
        return InternalUserContext(
            user=user,
            internal_role=row["role"]
        )

