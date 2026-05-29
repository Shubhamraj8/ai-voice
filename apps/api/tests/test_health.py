from unittest.mock import AsyncMock, patch

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


@patch("app.routes.health.ping_pool", new_callable=AsyncMock)
def test_health_endpoint(mock_ping_pool):
    mock_ping_pool.return_value = {"database": "ok"}

    # We must mock request.app.state.db_pool somehow.
    # The endpoint accesses `request.app.state.db_pool`
    # Let's mock the state so it doesn't fail before ping_pool is called.
    app.state.db_pool = AsyncMock()

    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert "database" in data
    assert data["database"] == "ok"
