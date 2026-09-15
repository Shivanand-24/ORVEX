import pytest
from fastapi.testclient import TestClient


@pytest.mark.anyio
async def test_create_user_success(client: TestClient) -> None:
    """Verify creating a valid global user identity returns HTTP 201 Created."""
    response = client.post(
        "/api/v1/users",
        json={"email": "alice@example.com", "full_name": "Alice Smith"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "alice@example.com"
    assert data["full_name"] == "Alice Smith"
    assert "id" in data


@pytest.mark.anyio
async def test_create_user_invalid_email(client: TestClient) -> None:
    """Verify creating a user with an invalid email returns HTTP 422 Unprocessable Entity."""
    response = client.post(
        "/api/v1/users",
        json={"email": "invalid-email-string", "full_name": "Bob Jones"},
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_user_duplicate_email_conflict(client: TestClient) -> None:
    """Verify creating a user with an existing email returns HTTP 409 Conflict."""
    client.post("/api/v1/users", json={"email": "duplicate@example.com", "full_name": "User 1"})
    response = client.post(
        "/api/v1/users",
        json={"email": "DUPLICATE@EXAMPLE.COM", "full_name": "User 2"},
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


@pytest.mark.anyio
async def test_list_users(client: TestClient) -> None:
    """Verify retrieving list of global users returns HTTP 200 OK."""
    client.post("/api/v1/users", json={"email": "u1@example.com", "full_name": "User One"})
    client.post("/api/v1/users", json={"email": "u2@example.com", "full_name": "User Two"})

    response = client.get("/api/v1/users")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


@pytest.mark.anyio
async def test_get_user_by_id(client: TestClient) -> None:
    """Verify retrieving a user by ID returns HTTP 200 OK."""
    created = client.post(
        "/api/v1/users", json={"email": "fetch@example.com", "full_name": "Fetch User"}
    ).json()

    response = client.get(f"/api/v1/users/{created['id']}")
    assert response.status_code == 200
    assert response.json()["email"] == "fetch@example.com"


@pytest.mark.anyio
async def test_get_user_not_found(client: TestClient) -> None:
    """Verify requesting a non-existent user ID returns HTTP 404 Not Found."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/api/v1/users/{fake_id}")
    assert response.status_code == 404
