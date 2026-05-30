import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app
from app.middleware.auth import InternalUserContext, User, require_internal_user
from fastapi import HTTPException
from fastapi.testclient import TestClient

client = TestClient(app)


def _internal_ctx():
    return InternalUserContext(
        user=User(id=uuid.uuid4(), email="internal@example.com"),
        internal_role="admin",
    )


@patch("app.routes.internal.log_internal_action", new_callable=AsyncMock)
@patch("app.routes.internal.get_service_role_client")
def test_internal_ping_success(mock_client_factory, mock_audit):
    mock_result = MagicMock()
    mock_result.count = 3
    mock_result.data = []
    table = mock_client_factory.return_value.table.return_value
    table.select.return_value.execute.return_value = mock_result

    app.dependency_overrides[require_internal_user] = _internal_ctx
    try:
        response = client.get(
            "/internal/ping",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["tenant_count"] == 3
        mock_audit.assert_awaited_once()
    finally:
        app.dependency_overrides.clear()


def test_internal_ping_forbidden():
    def deny():
        raise HTTPException(
            status_code=403,
            detail={
                "code": "not_internal",
                "message": "User does not have internal access",
            },
        )

    app.dependency_overrides[require_internal_user] = deny
    try:
        response = client.get(
            "/internal/ping",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "not_internal"
    finally:
        app.dependency_overrides.clear()
