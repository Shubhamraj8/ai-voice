"""Tests for manual onboarding invite (ticket 5.04). Supabase + DB + email mocked."""

import uuid
from unittest.mock import AsyncMock

import pytest
from app.services import onboarding
from fastapi import HTTPException


async def test_invite_tenant_login_success(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(onboarding, "get_pool", lambda: pool)
    conn.fetchrow.return_value = {"business_name": "Acme Clinic"}
    user_id = str(uuid.uuid4())
    invite = AsyncMock(return_value={"id": user_id, "email": "owner@acme.com"})
    monkeypatch.setattr(onboarding, "invite_user", invite)
    welcome = AsyncMock(return_value=True)
    monkeypatch.setattr(onboarding, "send_email", welcome)

    result = await onboarding.invite_tenant_login(uuid.uuid4(), "owner@acme.com")

    assert result == {"user_id": user_id, "email": "owner@acme.com"}
    # provisioned metadata so the signup trigger skips auto-tenant
    assert invite.await_args.kwargs["metadata"]["provisioned"] == "true"
    conn.execute.assert_awaited_once()  # tenant_users link
    welcome.assert_awaited_once()


async def test_invite_tenant_not_found(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(onboarding, "get_pool", lambda: pool)
    conn.fetchrow.return_value = None
    invite = AsyncMock()
    monkeypatch.setattr(onboarding, "invite_user", invite)

    with pytest.raises(HTTPException) as exc:
        await onboarding.invite_tenant_login(uuid.uuid4(), "owner@acme.com")

    assert exc.value.status_code == 404
    invite.assert_not_awaited()


async def test_invite_failure_returns_502(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(onboarding, "get_pool", lambda: pool)
    conn.fetchrow.return_value = {"business_name": "Acme"}
    monkeypatch.setattr(onboarding, "invite_user", AsyncMock(return_value=None))
    monkeypatch.setattr(onboarding, "send_email", AsyncMock())

    with pytest.raises(HTTPException) as exc:
        await onboarding.invite_tenant_login(uuid.uuid4(), "owner@acme.com")

    assert exc.value.status_code == 502
