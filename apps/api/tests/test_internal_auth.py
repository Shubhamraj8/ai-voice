import uuid
from unittest.mock import AsyncMock

import pytest
from app.config import get_settings
from app.middleware.auth import (
    InternalUserContext,
    User,
    _try_promote_founding_internal_user,
    require_internal_role,
    require_internal_user,
)
from fastapi import HTTPException


@pytest.fixture
def founding_env(monkeypatch):
    monkeypatch.setenv("INTERNAL_USER_EMAIL", "founder@zerqo.com")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_promote_founding_internal_user(founding_env):
    conn = AsyncMock()
    user = User(id=uuid.uuid4(), email="founder@zerqo.com")
    settings = get_settings()

    await _try_promote_founding_internal_user(conn, user, settings)

    conn.execute.assert_awaited_once()
    assert "INSERT INTO internal_users" in conn.execute.await_args.args[0]


@pytest.mark.asyncio
async def test_promote_skips_non_founding_email(founding_env):
    conn = AsyncMock()
    user = User(id=uuid.uuid4(), email="other@example.com")
    settings = get_settings()

    await _try_promote_founding_internal_user(conn, user, settings)

    conn.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_require_internal_role_blocks_support():
    admin_only = require_internal_role("admin")

    ctx = InternalUserContext(
        user=User(id=uuid.uuid4(), email="support@zerqo.com"),
        internal_role="support",
    )

    with pytest.raises(HTTPException) as exc:
        await admin_only(ctx)
    assert exc.value.status_code == 403
    assert exc.value.detail["code"] == "insufficient_internal_role"


@pytest.mark.asyncio
async def test_require_internal_user_promotes_founding(mock_db_pool, founding_env):
    pool, conn = mock_db_pool
    user = User(id=uuid.uuid4(), email="founder@zerqo.com")

    conn.fetchrow.side_effect = [None, {"role": "admin"}]

    ctx = await require_internal_user(user, pool=pool)

    assert ctx.internal_role == "admin"
    conn.execute.assert_awaited_once()
