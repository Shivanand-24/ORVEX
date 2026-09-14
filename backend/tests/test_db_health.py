from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_base_health_endpoint_remains_operational() -> None:
    """Verify GET /api/v1/health returns HTTP 200 OK regardless of DB status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "ORVEX API",
        "version": "v1",
    }


def test_database_health_endpoint_response() -> None:
    """Verify GET /api/v1/health/db returns 200 OK if DB connected or 503 if unavailable."""
    response = client.get("/api/v1/health/db")
    assert response.status_code in (200, 503)
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert data["database"] == "PostgreSQL"
    assert "connected" in data
