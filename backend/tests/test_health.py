from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check_status_code() -> None:
    """Verify that GET /api/v1/health returns HTTP 200 OK."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_health_check_response_structure() -> None:
    """Verify that GET /api/v1/health returns correct JSON schema structure."""
    response = client.get("/api/v1/health")
    data = response.json()
    assert data == {
        "status": "ok",
        "service": "ORVEX API",
        "version": "v1",
    }
