import uuid
import pytest
from fastapi.testclient import TestClient


@pytest.mark.anyio
async def test_create_knowledge_source_success(client: TestClient):
    # 1. Create Organization
    org_res = client.post("/api/v1/organizations", json={"name": "Knowledge Org", "slug": "knowledge-org"})
    assert org_res.status_code == 201
    org_id = org_res.json()["id"]

    # 2. Create Knowledge Source
    payload = {
        "organization_id": org_id,
        "name": "Engineering Runbooks",
        "description": "Standard operating procedures and troubleshooting guides.",
    }
    res = client.post("/api/v1/knowledge/sources", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Engineering Runbooks"
    assert data["description"] == "Standard operating procedures and troubleshooting guides."
    assert data["organization_id"] == org_id
    assert data["document_count"] == 0
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.anyio
async def test_create_knowledge_source_nonexistent_org(client: TestClient):
    random_org_id = str(uuid.uuid4())
    res = client.post(
        "/api/v1/knowledge/sources",
        json={"organization_id": random_org_id, "name": "Orphan Source"},
    )
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


@pytest.mark.anyio
async def test_create_knowledge_source_blank_name_rejected(client: TestClient):
    org_res = client.post("/api/v1/organizations", json={"name": "Blank Name Org", "slug": "blank-name-org"})
    org_id = org_res.json()["id"]

    res = client.post(
        "/api/v1/knowledge/sources",
        json={"organization_id": org_id, "name": "   "},
    )
    assert res.status_code in (400, 422)


@pytest.mark.anyio
async def test_list_knowledge_sources(client: TestClient):
    # Create two orgs
    org1_res = client.post("/api/v1/organizations", json={"name": "Org 1", "slug": "org-1"})
    org1_id = org1_res.json()["id"]
    org2_res = client.post("/api/v1/organizations", json={"name": "Org 2", "slug": "org-2"})
    org2_id = org2_res.json()["id"]

    # Create sources
    client.post("/api/v1/knowledge/sources", json={"organization_id": org1_id, "name": "Source 1A"})
    client.post("/api/v1/knowledge/sources", json={"organization_id": org1_id, "name": "Source 1B"})
    client.post("/api/v1/knowledge/sources", json={"organization_id": org2_id, "name": "Source 2A"})

    # List all
    all_res = client.get("/api/v1/knowledge/sources")
    assert all_res.status_code == 200
    all_names = [s["name"] for s in all_res.json()]
    assert "Source 1A" in all_names
    assert "Source 1B" in all_names
    assert "Source 2A" in all_names

    # List filtered by org1
    org1_sources_res = client.get(f"/api/v1/knowledge/sources?organization_id={org1_id}")
    assert org1_sources_res.status_code == 200
    org1_names = [s["name"] for s in org1_sources_res.json()]
    assert "Source 1A" in org1_names
    assert "Source 1B" in org1_names
    assert "Source 2A" not in org1_names


@pytest.mark.anyio
async def test_get_knowledge_source_by_id(client: TestClient):
    org_res = client.post("/api/v1/organizations", json={"name": "Get Org", "slug": "get-org"})
    org_id = org_res.json()["id"]

    source_res = client.post("/api/v1/knowledge/sources", json={"organization_id": org_id, "name": "Handbook"})
    source_id = source_res.json()["id"]

    res = client.get(f"/api/v1/knowledge/sources/{source_id}")
    assert res.status_code == 200
    assert res.json()["name"] == "Handbook"
    assert res.json()["id"] == source_id


@pytest.mark.anyio
async def test_get_knowledge_source_not_found(client: TestClient):
    random_id = str(uuid.uuid4())
    res = client.get(f"/api/v1/knowledge/sources/{random_id}")
    assert res.status_code == 404


@pytest.mark.anyio
async def test_update_knowledge_source(client: TestClient):
    org_res = client.post("/api/v1/organizations", json={"name": "Patch Org", "slug": "patch-org"})
    org_id = org_res.json()["id"]

    source_res = client.post("/api/v1/knowledge/sources", json={"organization_id": org_id, "name": "Old Name"})
    source_id = source_res.json()["id"]

    patch_res = client.patch(
        f"/api/v1/knowledge/sources/{source_id}",
        json={"name": "New Name", "description": "Updated Description"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "New Name"
    assert patch_res.json()["description"] == "Updated Description"


@pytest.mark.anyio
async def test_delete_knowledge_source(client: TestClient):
    org_res = client.post("/api/v1/organizations", json={"name": "Delete Org", "slug": "delete-org"})
    org_id = org_res.json()["id"]

    source_res = client.post("/api/v1/knowledge/sources", json={"organization_id": org_id, "name": "To Delete"})
    source_id = source_res.json()["id"]

    del_res = client.delete(f"/api/v1/knowledge/sources/{source_id}")
    assert del_res.status_code == 204

    # Verify deleted
    get_res = client.get(f"/api/v1/knowledge/sources/{source_id}")
    assert get_res.status_code == 404


@pytest.mark.anyio
async def test_cross_organization_source_isolation(client: TestClient):
    # Org A & Source A
    org_a_res = client.post("/api/v1/organizations", json={"name": "Org A", "slug": "org-a"})
    org_a_id = org_a_res.json()["id"]
    source_a_res = client.post("/api/v1/knowledge/sources", json={"organization_id": org_a_id, "name": "Source A"})
    source_a_id = source_a_res.json()["id"]

    # Org B
    org_b_res = client.post("/api/v1/organizations", json={"name": "Org B", "slug": "org-b"})
    org_b_id = org_b_res.json()["id"]

    # Accessing Source A while scoped to Org B MUST fail with 404
    cross_get = client.get(f"/api/v1/knowledge/sources/{source_a_id}?organization_id={org_b_id}")
    assert cross_get.status_code == 404

    # Updating Source A while scoped to Org B MUST fail with 404
    cross_patch = client.patch(
        f"/api/v1/knowledge/sources/{source_a_id}?organization_id={org_b_id}",
        json={"name": "Hijacked"},
    )
    assert cross_patch.status_code == 404

    # Deleting Source A while scoped to Org B MUST fail with 404
    cross_del = client.delete(f"/api/v1/knowledge/sources/{source_a_id}?organization_id={org_b_id}")
    assert cross_del.status_code == 404

    # Source A must still exist under Org A
    check_source = client.get(f"/api/v1/knowledge/sources/{source_a_id}?organization_id={org_a_id}")
    assert check_source.status_code == 200
    assert check_source.json()["name"] == "Source A"
