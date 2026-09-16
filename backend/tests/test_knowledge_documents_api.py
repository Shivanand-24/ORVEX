import uuid
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def setup_org_and_source(client: TestClient):
    org_res = client.post("/api/v1/organizations", json={"name": "Doc Org", "slug": "doc-org"})
    org_id = org_res.json()["id"]

    source_res = client.post(
        "/api/v1/knowledge/sources",
        json={"organization_id": org_id, "name": "Doc Source", "description": "Source for docs"},
    )
    source_id = source_res.json()["id"]
    return {"org_id": org_id, "source_id": source_id}


@pytest.mark.anyio
async def test_create_document_success(client: TestClient, setup_org_and_source):
    source_id = setup_org_and_source["source_id"]
    org_id = setup_org_and_source["org_id"]

    payload = {
        "name": "Architecture Spec",
        "file_type": "PDF",
        "size_bytes": 1048576,
        "summary": "Technical system architecture overview.",
    }
    res = client.post(f"/api/v1/knowledge/sources/{source_id}/documents", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Architecture Spec"
    assert data["file_type"] == "PDF"
    assert data["size_bytes"] == 1048576
    assert data["processing_status"] == "pending"
    assert data["indexing_status"] == "not_indexed"
    assert data["status"] == "Pending"
    assert data["readiness"] == "NotIndexed"
    assert data["source_id"] == source_id
    assert data["organization_id"] == org_id
    assert "storage://sources/" in data["storage_path"]
    assert "id" in data


@pytest.mark.anyio
async def test_create_document_nonexistent_source(client: TestClient):
    random_id = str(uuid.uuid4())
    res = client.post(
        f"/api/v1/knowledge/sources/{random_id}/documents",
        json={"name": "Ghost Document"},
    )
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


@pytest.mark.anyio
async def test_create_document_source_org_mismatch_rejected(client: TestClient, setup_org_and_source):
    source_id = setup_org_and_source["source_id"]

    # Create another org
    other_org = client.post("/api/v1/organizations", json={"name": "Other Org", "slug": "other-org"}).json()
    other_org_id = other_org["id"]

    # Attempt to attach document with mismatched explicit organization_id
    res = client.post(
        f"/api/v1/knowledge/sources/{source_id}/documents",
        json={"name": "Mismatched Doc", "organization_id": other_org_id},
    )
    assert res.status_code == 400
    assert "mismatch" in res.json()["detail"].lower() or "does not belong" in res.json()["detail"].lower()


@pytest.mark.anyio
async def test_list_documents_for_source(client: TestClient, setup_org_and_source):
    source_id = setup_org_and_source["source_id"]

    client.post(f"/api/v1/knowledge/sources/{source_id}/documents", json={"name": "Doc Alpha"})
    client.post(f"/api/v1/knowledge/sources/{source_id}/documents", json={"name": "Doc Beta"})

    res = client.get(f"/api/v1/knowledge/sources/{source_id}/documents")
    assert res.status_code == 200
    docs = res.json()
    doc_names = [d["name"] for d in docs]
    assert "Doc Alpha" in doc_names
    assert "Doc Beta" in doc_names


@pytest.mark.anyio
async def test_get_document_by_id(client: TestClient, setup_org_and_source):
    source_id = setup_org_and_source["source_id"]
    create_res = client.post(f"/api/v1/knowledge/sources/{source_id}/documents", json={"name": "Single Doc"})
    doc_id = create_res.json()["id"]

    res = client.get(f"/api/v1/knowledge/documents/{doc_id}")
    assert res.status_code == 200
    assert res.json()["name"] == "Single Doc"
    assert res.json()["id"] == doc_id


@pytest.mark.anyio
async def test_get_document_not_found(client: TestClient):
    random_id = str(uuid.uuid4())
    res = client.get(f"/api/v1/knowledge/documents/{random_id}")
    assert res.status_code == 404


@pytest.mark.anyio
async def test_update_document(client: TestClient, setup_org_and_source):
    source_id = setup_org_and_source["source_id"]
    create_res = client.post(f"/api/v1/knowledge/sources/{source_id}/documents", json={"name": "Draft Doc"})
    doc_id = create_res.json()["id"]

    patch_res = client.patch(
        f"/api/v1/knowledge/documents/{doc_id}",
        json={"name": "Final Doc", "summary": "Approved for general release"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "Final Doc"
    assert patch_res.json()["summary"] == "Approved for general release"


@pytest.mark.anyio
async def test_delete_document(client: TestClient, setup_org_and_source):
    source_id = setup_org_and_source["source_id"]
    create_res = client.post(f"/api/v1/knowledge/sources/{source_id}/documents", json={"name": "Trash Doc"})
    doc_id = create_res.json()["id"]

    del_res = client.delete(f"/api/v1/knowledge/documents/{doc_id}")
    assert del_res.status_code == 204

    # Verify deleted
    get_res = client.get(f"/api/v1/knowledge/documents/{doc_id}")
    assert get_res.status_code == 404

    # Source and org still exist
    source_res = client.get(f"/api/v1/knowledge/sources/{source_id}")
    assert source_res.status_code == 200


@pytest.mark.anyio
async def test_lifecycle_status_persistence(client: TestClient, setup_org_and_source):
    source_id = setup_org_and_source["source_id"]

    # 1. Create with initial pending/not_indexed
    create_res = client.post(
        f"/api/v1/knowledge/sources/{source_id}/documents",
        json={"name": "Lifecycle Doc", "status": "Pending"},
    )
    doc_id = create_res.json()["id"]
    assert create_res.json()["status"] == "Pending"
    assert create_res.json()["readiness"] == "NotIndexed"

    # 2. Transition processing to Processing
    p1 = client.patch(f"/api/v1/knowledge/documents/{doc_id}", json={"status": "Processing"})
    assert p1.status_code == 200
    assert p1.json()["status"] == "Processing"
    assert p1.json()["processing_status"] == "processing"

    # 3. Complete processing to Processed
    p2 = client.patch(f"/api/v1/knowledge/documents/{doc_id}", json={"status": "Processed"})
    assert p2.status_code == 200
    assert p2.json()["status"] == "Processed"
    assert p2.json()["processing_status"] == "processed"

    # 4. Transition readiness to Indexing
    p3 = client.patch(f"/api/v1/knowledge/documents/{doc_id}", json={"readiness": "Indexing"})
    assert p3.status_code == 200
    assert p3.json()["readiness"] == "Indexing"
    assert p3.json()["indexing_status"] == "indexing"

    # 5. Complete indexing to Indexed
    p4 = client.patch(f"/api/v1/knowledge/documents/{doc_id}", json={"readiness": "Indexed"})
    assert p4.status_code == 200
    assert p4.json()["readiness"] == "Indexed"
    assert p4.json()["indexing_status"] == "indexed"


@pytest.mark.anyio
async def test_lifecycle_transition_validation(client: TestClient, setup_org_and_source):
    source_id = setup_org_and_source["source_id"]

    # 1. Attempt to start indexing while document is still 'pending'
    create_res = client.post(
        f"/api/v1/knowledge/sources/{source_id}/documents",
        json={"name": "Invalid Transition Doc", "status": "Pending"},
    )
    doc_id = create_res.json()["id"]

    bad_idx = client.patch(
        f"/api/v1/knowledge/documents/{doc_id}",
        json={"readiness": "Indexing"},
    )
    assert bad_idx.status_code == 400
    assert "must be in 'processed' state" in bad_idx.json()["detail"].lower()

    # 2. Attempt invalid lifecycle status string
    bad_status = client.patch(
        f"/api/v1/knowledge/documents/{doc_id}",
        json={"status": "InvalidStatusXYZ"},
    )
    assert bad_status.status_code in (400, 422)


@pytest.mark.anyio
async def test_cross_organization_document_isolation(client: TestClient):
    # Org A, Source A, Doc A
    org_a = client.post("/api/v1/organizations", json={"name": "Org A", "slug": "org-a-iso"}).json()
    source_a = client.post("/api/v1/knowledge/sources", json={"organization_id": org_a["id"], "name": "Source A"}).json()
    doc_a = client.post(f"/api/v1/knowledge/sources/{source_a['id']}/documents", json={"name": "Doc A"}).json()

    # Org B, Source B
    org_b = client.post("/api/v1/organizations", json={"name": "Org B", "slug": "org-b-iso"}).json()
    source_b = client.post("/api/v1/knowledge/sources", json={"organization_id": org_b["id"], "name": "Source B"}).json()

    # Org B cannot access Doc A via direct GET
    iso_get = client.get(f"/api/v1/knowledge/documents/{doc_a['id']}?organization_id={org_b['id']}")
    assert iso_get.status_code == 404

    # Org B cannot access Doc A via list on Source A
    iso_list = client.get(f"/api/v1/knowledge/sources/{source_a['id']}/documents?organization_id={org_b['id']}")
    assert iso_list.status_code == 404

    # Org B cannot update Doc A
    iso_patch = client.patch(
        f"/api/v1/knowledge/documents/{doc_a['id']}?organization_id={org_b['id']}",
        json={"name": "Tampered"},
    )
    assert iso_patch.status_code == 404

    # Org B cannot delete Doc A
    iso_delete = client.delete(f"/api/v1/knowledge/documents/{doc_a['id']}?organization_id={org_b['id']}")
    assert iso_delete.status_code == 404

    # Org B cannot attach Doc to Source A
    iso_attach = client.post(
        f"/api/v1/knowledge/sources/{source_a['id']}/documents?organization_id={org_b['id']}",
        json={"name": "Intruder Doc"},
    )
    assert iso_attach.status_code == 400


@pytest.mark.anyio
async def test_cascade_delete_source_deletes_documents(client: TestClient, setup_org_and_source):
    source_id = setup_org_and_source["source_id"]

    doc_res = client.post(f"/api/v1/knowledge/sources/{source_id}/documents", json={"name": "Cascade Doc"})
    doc_id = doc_res.json()["id"]

    # Delete source
    del_res = client.delete(f"/api/v1/knowledge/sources/{source_id}")
    assert del_res.status_code == 204

    # Document must be gone
    doc_get = client.get(f"/api/v1/knowledge/documents/{doc_id}")
    assert doc_get.status_code == 404
