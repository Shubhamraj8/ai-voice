import json
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from app.db.pool import get_pool
from app.main import app
from app.middleware.auth import InternalUserContext, User, require_internal_user
from app.models.tenant import ProviderConfig
from app.providers.registry import validate_provider_config
from fastapi.testclient import TestClient

client = TestClient(app)


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


def test_validate_provider_config_rejects_unknown():
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        validate_provider_config(
            ProviderConfig(stt="not_real", tts="inworld", llm="deepseek_native")
        )
    assert exc.value.detail["code"] == "invalid_provider_config"


def test_list_tenants_requires_internal():
    response = client.get("/internal/tenants")
    assert response.status_code == 401


def test_list_tenants_success(internal_api, mock_db_pool):
    pool, conn = mock_db_pool
    tenant_id = uuid.uuid4()
    now = datetime.now(UTC)

    conn.fetchrow.return_value = {"total": 1}
    conn.fetch.return_value = [
        {
            "id": tenant_id,
            "slug": "acme",
            "business_name": "Acme Corp",
            "market": "india_english",
            "status": "active",
            "plan": "starter",
            "contact_email": "ops@acme.com",
            "contact_phone": "+919999999999",
            "created_at": now,
            "agent_count": 2,
            "calls_last_7d": 5,
            "mrr_usd": 0.0,
        }
    ]

    app.dependency_overrides[get_pool] = lambda: pool
    try:
        response = client.get("/internal/tenants?search=acme")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["business_name"] == "Acme Corp"
    finally:
        app.dependency_overrides.pop(get_pool, None)


def test_create_tenant_invalid_provider(internal_api, mock_db_pool):
    pool, _conn = mock_db_pool
    app.dependency_overrides[get_pool] = lambda: pool
    try:
        response = client.post(
            "/internal/tenants",
            json={
                "slug": "bad-co",
                "business_name": "Bad Co",
                "provider_config": {
                    "stt": "nope",
                    "tts": "inworld",
                    "llm": "deepseek_native",
                },
            },
        )
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "invalid_provider_config"
    finally:
        app.dependency_overrides.pop(get_pool, None)


def test_create_tenant_success(internal_api, mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    tenant_id = uuid.uuid4()
    now = datetime.now(UTC)

    conn.fetchrow.side_effect = [
        None,
        {
            "id": tenant_id,
            "slug": "new-co",
            "business_name": "New Co",
            "market": "india_english",
            "language": "en",
            "timezone": "Asia/Kolkata",
            "plan": "starter",
            "provider_config": json.dumps(
                {"stt": "cartesia", "tts": "inworld", "llm": "deepseek_native"}
            ),
            "onboarding_mode": "sales_led",
            "status": "active",
            "contact_email": None,
            "contact_name": None,
            "contact_phone": None,
            "archived_at": None,
            "created_at": now,
            "updated_at": now,
        },
    ]

    audit = AsyncMock()
    monkeypatch.setattr("app.routes.internal_tenants.log_internal_action", audit)
    app.dependency_overrides[get_pool] = lambda: pool
    try:
        response = client.post(
            "/internal/tenants",
            json={
                "slug": "new-co",
                "business_name": "New Co",
                "market": "india_english",
            },
        )
        assert response.status_code == 201
        assert response.json()["slug"] == "new-co"
        audit.assert_awaited_once()
    finally:
        app.dependency_overrides.pop(get_pool, None)
