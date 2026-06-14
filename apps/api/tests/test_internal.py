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


def test_internal_latency_success():
    sample = {
        "sample_size": 2,
        "stt_ms": {"p50": 100, "p95": 120, "p99": 140},
        "llm_ms": {"p50": 300, "p95": 400, "p99": 500},
        "tts_first_byte_ms": {"p50": 200, "p95": 250, "p99": 300},
        "total_ms": {"p50": 700, "p95": 900, "p99": 1100},
    }
    with patch(
        "app.routes.internal.latency_percentiles",
        new_callable=AsyncMock,
        return_value=sample,
    ):
        app.dependency_overrides[require_internal_user] = _internal_ctx
        try:
            response = client.get(
                "/internal/latency",
                headers={"Authorization": "Bearer test-token"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["sample_size"] == 2
            assert data["total_ms"]["p95"] == 900
        finally:
            app.dependency_overrides.clear()


def test_internal_agents_success():
    with patch("app.routes.internal.agent_registry") as mock_registry:
        mock_registry.active_count.return_value = 2
        mock_registry.list_active.return_value = [
            {"call_sid": "CA1", "age_secs": 30},
            {"call_sid": "CA2", "age_secs": 90},
        ]

        app.dependency_overrides[require_internal_user] = _internal_ctx
        try:
            response = client.get(
                "/internal/agents",
                headers={"Authorization": "Bearer test-token"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["active_count"] == 2
            assert len(data["agents"]) == 2
            assert data["agents"][0]["call_sid"] == "CA1"
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
