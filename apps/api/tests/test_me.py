import uuid
from datetime import datetime

from app.main import app
from app.middleware.auth import (
    TenantContext,
    User,
    get_current_tenant,
    get_current_user,
)
from app.models.tenant import ProviderConfig, Tenant, TenantMarket, TenantOnboardingMode
from app.models.user import TenantUserRole
from fastapi.testclient import TestClient

client = TestClient(app)


def mock_get_current_user():
    return User(id=uuid.uuid4(), email="test@example.com", role="authenticated")


def mock_get_current_tenant():
    return TenantContext(
        tenant=Tenant(
            id=uuid.uuid4(),
            slug="test-tenant",
            business_name="Test Business",
            market=TenantMarket.INDIA_ENGLISH,
            language="en",
            timezone="Asia/Kolkata",
            plan="starter",
            provider_config=ProviderConfig(
                stt="cartesia", tts="inworld", llm="deepseek_native"
            ),
            onboarding_mode=TenantOnboardingMode.SELF_SERVE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        role=TenantUserRole.OWNER,
    )


def test_me_unauthenticated():
    response = client.get("/me")
    assert response.status_code == 403 or response.status_code == 401


def test_me_authenticated():
    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[get_current_tenant] = mock_get_current_tenant

    try:
        response = client.get("/me")
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "tenant" in data
        assert "role" in data
        assert data["role"] == "owner"
        assert data["tenant"]["slug"] == "test-tenant"
    finally:
        app.dependency_overrides.clear()
