"""Tests for the agent CRUD API (ticket 3.07). DB mocked."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from app.db.pool import get_pool
from app.main import app
from app.middleware.auth import InternalUserContext, User, require_internal_user
from fastapi.testclient import TestClient

client = TestClient(app)

VALID_VOICE = "aura-asteria-en"


def _internal_ctx():
    return InternalUserContext(
        user=User(id=uuid.uuid4(), email="internal@example.com"),
        internal_role="admin",
    )


@pytest.fixture
def internal_api():
    app.dependency_overrides[require_internal_user] = _internal_ctx
    yield
    app.dependency_overrides.clear()


def _agent_row(agent_id, tenant_id, now, *, archived_at=None, is_active=True):
    return {
        "id": agent_id,
        "tenant_id": tenant_id,
        "name": "Main line",
        "starter_prompt": "receptionist",
        "system_prompt": "You are a helpful AI receptionist.",
        "tools": [],
        "voice_id": VALID_VOICE,
        "phone_number": "+911234567890",
        "twilio_sid": "PN123",
        "is_active": is_active,
        "version": 1,
        "archived_at": archived_at,
        "created_at": now,
        "updated_at": now,
    }


def _create_body(**overrides):
    body = {
        "name": "Front desk",
        "system_prompt": "You are a receptionist.",
        "voice_id": VALID_VOICE,
        "phone_number": "+911234567890",
        "twilio_sid": "PN123",
    }
    body.update(overrides)
    return body


def test_create_agent_success(internal_api, mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    tenant_id = uuid.uuid4()
    agent_id = uuid.uuid4()
    now = datetime.now(UTC)

    # phone-number uniqueness check (None), then INSERT RETURNING
    conn.fetchrow.side_effect = [None, _agent_row(agent_id, tenant_id, now)]
    audit = AsyncMock()
    monkeypatch.setattr("app.routes.internal_agents.log_internal_action", audit)

    app.dependency_overrides[get_pool] = lambda: pool
    try:
        response = client.post(
            f"/internal/tenants/{tenant_id}/agents", json=_create_body()
        )
        assert response.status_code == 201
        assert response.json()["voice_id"] == VALID_VOICE
        audit.assert_awaited_once()
    finally:
        app.dependency_overrides.pop(get_pool, None)


def test_create_agent_invalid_voice_returns_422(internal_api, mock_db_pool):
    pool, _conn = mock_db_pool
    tenant_id = uuid.uuid4()

    app.dependency_overrides[get_pool] = lambda: pool
    try:
        response = client.post(
            f"/internal/tenants/{tenant_id}/agents",
            json=_create_body(voice_id="not-a-real-voice"),
        )
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert detail["code"] == "invalid_voice_id"
        assert VALID_VOICE in detail["allowed"]
    finally:
        app.dependency_overrides.pop(get_pool, None)


def test_create_agent_long_system_prompt_returns_422(internal_api, mock_db_pool):
    pool, _conn = mock_db_pool
    tenant_id = uuid.uuid4()

    app.dependency_overrides[get_pool] = lambda: pool
    try:
        response = client.post(
            f"/internal/tenants/{tenant_id}/agents",
            json=_create_body(system_prompt="x" * 4001),
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.pop(get_pool, None)


def test_list_agents(internal_api, mock_db_pool):
    pool, conn = mock_db_pool
    tenant_id = uuid.uuid4()
    now = datetime.now(UTC)
    conn.fetch.return_value = [_agent_row(uuid.uuid4(), tenant_id, now)]

    app.dependency_overrides[get_pool] = lambda: pool
    try:
        response = client.get(f"/internal/tenants/{tenant_id}/agents")
        assert response.status_code == 200
        assert len(response.json()) == 1
    finally:
        app.dependency_overrides.pop(get_pool, None)


def test_patch_agent(internal_api, mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    tenant_id = uuid.uuid4()
    agent_id = uuid.uuid4()
    now = datetime.now(UTC)

    updated = _agent_row(agent_id, tenant_id, now)
    updated["name"] = "Reception"
    # scoped fetch (tenant matches), then UPDATE RETURNING
    conn.fetchrow.side_effect = [_agent_row(agent_id, tenant_id, now), updated]
    audit = AsyncMock()
    monkeypatch.setattr("app.routes.internal_agents.log_internal_action", audit)

    app.dependency_overrides[get_pool] = lambda: pool
    try:
        response = client.patch(
            f"/internal/tenants/{tenant_id}/agents/{agent_id}",
            json={"name": "Reception"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Reception"
        audit.assert_awaited_once()
    finally:
        app.dependency_overrides.pop(get_pool, None)


def test_soft_delete_agent(internal_api, mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    tenant_id = uuid.uuid4()
    agent_id = uuid.uuid4()
    now = datetime.now(UTC)

    archived = _agent_row(agent_id, tenant_id, now, archived_at=now, is_active=False)
    conn.fetchrow.side_effect = [_agent_row(agent_id, tenant_id, now), archived]
    audit = AsyncMock()
    monkeypatch.setattr("app.routes.internal_agents.log_internal_action", audit)

    app.dependency_overrides[get_pool] = lambda: pool
    try:
        response = client.delete(f"/internal/tenants/{tenant_id}/agents/{agent_id}")
        assert response.status_code == 200
        assert response.json()["is_active"] is False
        assert response.json()["archived_at"] is not None
        audit.assert_awaited_once()
    finally:
        app.dependency_overrides.pop(get_pool, None)


def test_cross_tenant_access_returns_403(internal_api, mock_db_pool):
    pool, conn = mock_db_pool
    path_tenant = uuid.uuid4()
    other_tenant = uuid.uuid4()
    agent_id = uuid.uuid4()
    now = datetime.now(UTC)

    # The agent belongs to a different tenant than the URL's tenant_id.
    conn.fetchrow.side_effect = [_agent_row(agent_id, other_tenant, now)]

    app.dependency_overrides[get_pool] = lambda: pool
    try:
        response = client.patch(
            f"/internal/tenants/{path_tenant}/agents/{agent_id}",
            json={"name": "Hijack"},
        )
        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "cross_tenant"
    finally:
        app.dependency_overrides.pop(get_pool, None)
