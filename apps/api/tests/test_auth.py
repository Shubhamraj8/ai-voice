import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from app.middleware.auth import (
    JWKS_CACHE,
    User,
    get_current_tenant,
    get_current_user,
    get_jwks,
)
from fastapi import HTTPException


@pytest.fixture(autouse=True)
def reset_jwks_cache():
    JWKS_CACHE["keys"] = {}
    JWKS_CACHE["expires_at"] = 0
    yield
    JWKS_CACHE["keys"] = {}
    JWKS_CACHE["expires_at"] = 0


@pytest.mark.asyncio
async def test_get_current_user_missing_token():
    with pytest.raises(HTTPException) as exc:
        await get_current_user(None)
    assert exc.value.status_code == 401
    assert exc.value.detail["code"] == "missing_token"


@pytest.mark.asyncio
async def test_get_current_user_expired_token():
    creds = MagicMock()
    creds.credentials = "fake.jwt.token"
    with patch(
        "app.middleware.auth.jwt.get_unverified_header",
        return_value={"kid": "k1"},
    ):
        with patch("app.middleware.auth.get_jwks", new_callable=AsyncMock) as mock_jwks:
            mock_jwks.return_value = {
                "k1": {"kid": "k1", "kty": "RSA", "n": "x", "e": "AQAB"}
            }
            with patch(
                "app.middleware.auth._public_key_and_algorithms",
                return_value=("key", ["ES256"]),
            ):
                with patch(
                    "app.middleware.auth.jwt.decode",
                    side_effect=jwt.ExpiredSignatureError,
                ):
                    with pytest.raises(HTTPException) as exc:
                        await get_current_user(creds)
    assert exc.value.status_code == 401
    assert exc.value.detail["code"] == "token_expired"


@pytest.mark.asyncio
async def test_get_current_tenant_no_membership(mock_db_pool):
    pool, conn = mock_db_pool
    conn.fetchrow.return_value = None
    user = User(id=uuid.uuid4(), email="x@y.com")

    with pytest.raises(HTTPException) as exc:
        await get_current_tenant(user, pool=pool)
    assert exc.value.status_code == 403
    assert exc.value.detail["code"] == "no_tenant"


@pytest.mark.asyncio
async def test_jwks_cache_fetches_once():
    with patch("app.middleware.auth.fetch_jwks", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = {"keys": [{"kid": "abc", "kty": "RSA"}]}
        await get_jwks()
        await get_jwks()
        assert mock_fetch.await_count == 1
