import pytest
from fastapi.testclient import TestClient


@pytest.mark.anyio
async def test_add_member_success(client: TestClient) -> None:
    """Verify adding a user to an organization returns HTTP 201 Created."""
    org = client.post("/api/v1/organizations", json={"name": "Org Corp"}).json()
    user = client.post("/api/v1/users", json={"email": "m1@example.com", "full_name": "Member One"}).json()

    response = client.post(
        f"/api/v1/organizations/{org['id']}/members",
        json={"user_id": user["id"], "role": "admin"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["organization_id"] == org["id"]
    assert data["user_id"] == user["id"]
    assert data["role"] == "admin"
    assert data["user"]["email"] == "m1@example.com"


@pytest.mark.anyio
async def test_add_member_duplicate_conflict(client: TestClient) -> None:
    """Verify adding the same user to the same organization twice returns HTTP 409 Conflict."""
    org = client.post("/api/v1/organizations", json={"name": "Dup Org"}).json()
    user = client.post("/api/v1/users", json={"email": "dup@example.com", "full_name": "Dup User"}).json()

    client.post(
        f"/api/v1/organizations/{org['id']}/members",
        json={"user_id": user["id"], "role": "member"},
    )

    response = client.post(
        f"/api/v1/organizations/{org['id']}/members",
        json={"user_id": user["id"], "role": "analyst"},
    )
    assert response.status_code == 409
    assert "already a member" in response.json()["detail"]


@pytest.mark.anyio
async def test_add_member_nonexistent_org(client: TestClient) -> None:
    """Verify adding a member to a non-existent organization returns HTTP 404 Not Found."""
    user = client.post("/api/v1/users", json={"email": "noorg@example.com", "full_name": "No Org"}).json()
    fake_org_id = "00000000-0000-0000-0000-000000000000"

    response = client.post(
        f"/api/v1/organizations/{fake_org_id}/members",
        json={"user_id": user["id"], "role": "member"},
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_add_member_nonexistent_user(client: TestClient) -> None:
    """Verify adding a non-existent user to an organization returns HTTP 404 Not Found."""
    org = client.post("/api/v1/organizations", json={"name": "No User Org"}).json()
    fake_user_id = "00000000-0000-0000-0000-000000000000"

    response = client.post(
        f"/api/v1/organizations/{org['id']}/members",
        json={"user_id": fake_user_id, "role": "member"},
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_add_member_invalid_role(client: TestClient) -> None:
    """Verify providing an invalid role returns HTTP 422 Unprocessable Entity."""
    org = client.post("/api/v1/organizations", json={"name": "Role Org"}).json()
    user = client.post("/api/v1/users", json={"email": "badrole@example.com", "full_name": "Bad Role"}).json()

    response = client.post(
        f"/api/v1/organizations/{org['id']}/members",
        json={"user_id": user["id"], "role": "superadmin"},
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_list_members(client: TestClient) -> None:
    """Verify listing organization members returns HTTP 200 OK."""
    org = client.post("/api/v1/organizations", json={"name": "List Org"}).json()
    u1 = client.post("/api/v1/users", json={"email": "l1@example.com", "full_name": "L1"}).json()
    u2 = client.post("/api/v1/users", json={"email": "l2@example.com", "full_name": "L2"}).json()

    client.post(f"/api/v1/organizations/{org['id']}/members", json={"user_id": u1["id"], "role": "admin"})
    client.post(f"/api/v1/organizations/{org['id']}/members", json={"user_id": u2["id"], "role": "analyst"})

    response = client.get(f"/api/v1/organizations/{org['id']}/members")
    assert response.status_code == 200
    members = response.json()
    assert len(members) == 2


@pytest.mark.anyio
async def test_update_member_role(client: TestClient) -> None:
    """Verify updating a member's role returns HTTP 200 OK."""
    org = client.post("/api/v1/organizations", json={"name": "Update Org"}).json()
    user = client.post("/api/v1/users", json={"email": "upd@example.com", "full_name": "Upd"}).json()
    mem = client.post(
        f"/api/v1/organizations/{org['id']}/members",
        json={"user_id": user["id"], "role": "member"},
    ).json()

    response = client.patch(
        f"/api/v1/organizations/{org['id']}/members/{mem['id']}",
        json={"role": "admin"},
    )
    assert response.status_code == 200
    assert response.json()["role"] == "admin"


@pytest.mark.anyio
async def test_delete_member_preserves_user_and_organization(client: TestClient) -> None:
    """Verify deleting a membership deletes ONLY the membership row, leaving user and org intact."""
    org = client.post("/api/v1/organizations", json={"name": "Del Org"}).json()
    user = client.post("/api/v1/users", json={"email": "del@example.com", "full_name": "Del User"}).json()
    mem = client.post(
        f"/api/v1/organizations/{org['id']}/members",
        json={"user_id": user["id"], "role": "member"},
    ).json()

    # Delete membership
    del_resp = client.delete(f"/api/v1/organizations/{org['id']}/members/{mem['id']}")
    assert del_resp.status_code == 204

    # Verify membership list is now empty
    list_resp = client.get(f"/api/v1/organizations/{org['id']}/members")
    assert len(list_resp.json()) == 0

    # Verify user and organization still exist!
    assert client.get(f"/api/v1/users/{user['id']}").status_code == 200
    assert client.get(f"/api/v1/organizations/{org['id']}").status_code == 200


@pytest.mark.anyio
async def test_cross_organization_membership_access_rejection(client: TestClient) -> None:
    """Verify modifying Org B's membership via Org A's URL path is rejected with HTTP 404 Not Found."""
    org_a = client.post("/api/v1/organizations", json={"name": "Org A"}).json()
    org_b = client.post("/api/v1/organizations", json={"name": "Org B"}).json()

    user = client.post("/api/v1/users", json={"email": "cross@example.com", "full_name": "Cross User"}).json()
    mem_b = client.post(
        f"/api/v1/organizations/{org_b['id']}/members",
        json={"user_id": user["id"], "role": "member"},
    ).json()

    # Attempt to update Org B's membership through Org A's endpoint
    response = client.patch(
        f"/api/v1/organizations/{org_a['id']}/members/{mem_b['id']}",
        json={"role": "admin"},
    )
    assert response.status_code == 404
    assert "does not belong to organization" in response.json()["detail"]

    # Attempt to delete Org B's membership through Org A's endpoint
    del_response = client.delete(f"/api/v1/organizations/{org_a['id']}/members/{mem_b['id']}")
    assert del_response.status_code == 404
