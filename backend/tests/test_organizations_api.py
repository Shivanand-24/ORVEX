import pytest
from fastapi.testclient import TestClient


@pytest.mark.anyio
async def test_create_organization_success(client: TestClient) -> None:
    """Verify creating a valid organization returns HTTP 201 Created."""
    response = client.post(
        "/api/v1/organizations",
        json={"name": "Acme Corp", "slug": "acme-corp"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Acme Corp"
    assert data["slug"] == "acme-corp"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.anyio
async def test_create_organization_auto_slug(client: TestClient) -> None:
    """Verify creating an organization generates an auto-slug if omitted."""
    response = client.post(
        "/api/v1/organizations",
        json={"name": "Stark Industries & Co."},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["slug"] == "stark-industries-co"


@pytest.mark.anyio
async def test_create_organization_blank_name_rejected(client: TestClient) -> None:
    """Verify creating an organization with a blank name returns HTTP 422 Unprocessable Entity."""
    response = client.post(
        "/api/v1/organizations",
        json={"name": "   "},
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_organization_duplicate_slug_conflict(client: TestClient) -> None:
    """Verify creating an organization with a duplicate slug returns HTTP 409 Conflict."""
    client.post("/api/v1/organizations", json={"name": "Org One", "slug": "shared-slug"})
    response = client.post(
        "/api/v1/organizations",
        json={"name": "Org Two", "slug": "shared-slug"},
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


@pytest.mark.anyio
async def test_list_organizations(client: TestClient) -> None:
    """Verify retrieving list of organizations returns HTTP 200 OK."""
    client.post("/api/v1/organizations", json={"name": "Alpha Inc", "slug": "alpha-inc"})
    client.post("/api/v1/organizations", json={"name": "Beta LLC", "slug": "beta-llc"})

    response = client.get("/api/v1/organizations")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


@pytest.mark.anyio
async def test_get_organization_by_id(client: TestClient) -> None:
    """Verify retrieving a single organization by ID returns HTTP 200 OK."""
    created = client.post(
        "/api/v1/organizations", json={"name": "Gamma Corp", "slug": "gamma-corp"}
    ).json()

    response = client.get(f"/api/v1/organizations/{created['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == "Gamma Corp"


@pytest.mark.anyio
async def test_get_organization_not_found(client: TestClient) -> None:
    """Verify requesting a non-existent organization ID returns HTTP 404 Not Found."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/api/v1/organizations/{fake_id}")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_update_organization(client: TestClient) -> None:
    """Verify updating organization name and slug returns HTTP 200 OK."""
    created = client.post(
        "/api/v1/organizations", json={"name": "Original Name", "slug": "original-slug"}
    ).json()

    response = client.patch(
        f"/api/v1/organizations/{created['id']}",
        json={"name": "Updated Name", "slug": "updated-slug"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["slug"] == "updated-slug"
