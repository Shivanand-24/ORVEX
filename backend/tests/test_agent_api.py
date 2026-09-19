import uuid
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def setup_tenants(client: TestClient):
    # Org 1 with User 1 and Knowledge Source 1
    org1_res = client.post("/api/v1/organizations", json={"name": "Alpha Corp", "slug": "alpha-corp"})
    org1_id = org1_res.json()["id"]

    user1_res = client.post("/api/v1/users", json={"email": "alpha_lead@alpha.com", "full_name": "Alpha Lead"})
    user1_id = user1_res.json()["id"]

    client.post(f"/api/v1/organizations/{org1_id}/members", json={"user_id": user1_id, "role": "admin"})

    ks1_res = client.post("/api/v1/knowledge/sources", json={"organization_id": org1_id, "name": "Alpha Handbook"})
    ks1_id = ks1_res.json()["id"]

    # Org 2 with User 2 and Knowledge Source 2
    org2_res = client.post("/api/v1/organizations", json={"name": "Beta Inc", "slug": "beta-inc"})
    org2_id = org2_res.json()["id"]

    user2_res = client.post("/api/v1/users", json={"email": "beta_lead@beta.com", "full_name": "Beta Lead"})
    user2_id = user2_res.json()["id"]

    client.post(f"/api/v1/organizations/{org2_id}/members", json={"user_id": user2_id, "role": "admin"})

    ks2_res = client.post("/api/v1/knowledge/sources", json={"organization_id": org2_id, "name": "Beta Runbook"})
    ks2_id = ks2_res.json()["id"]

    return {
        "org1_id": org1_id,
        "user1_id": user1_id,
        "ks1_id": ks1_id,
        "org2_id": org2_id,
        "user2_id": user2_id,
        "ks2_id": ks2_id,
    }


# ==========================================
# Agent CRUD Tests
# ==========================================

@pytest.mark.anyio
async def test_create_agent_minimal(client: TestClient, setup_tenants):
    org_id = setup_tenants["org1_id"]
    payload = {
        "organization_id": org_id,
        "name": "Research Sentinel",
        "description": "Performs deep document synthesis.",
        "domain": "Research",
        "system_instructions": "Analyze input documents and output findings.",
    }
    res = client.post("/api/v1/agents", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Research Sentinel"
    assert data["domain"] == "Research"
    assert data["status"] == "Active"
    assert data["require_approval"] is False
    assert data["organization_id"] == org_id
    assert data["created_by_user_id"] == setup_tenants["user1_id"]
    assert data["tools"] == []
    assert data["knowledge_source_ids"] == []
    assert data["executions"] == 0
    assert data["success_rate"] == "100%"
    assert data["last_run"] == "Never"


@pytest.mark.anyio
async def test_create_agent_with_initial_tools_and_knowledge_sources(client: TestClient, setup_tenants):
    org_id = setup_tenants["org1_id"]
    user_id = setup_tenants["user1_id"]
    ks1_id = setup_tenants["ks1_id"]

    payload = {
        "organization_id": org_id,
        "created_by_user_id": user_id,
        "name": "Compliance Auditor",
        "description": "Audits access lists.",
        "domain": "Security",
        "status": "Active",
        "system_instructions": "Check all IAM roles.",
        "require_approval": True,
        "tools": ["Access Control Analyzer", "Compliance Check"],
        "knowledge_source_ids": [ks1_id],
    }
    res = client.post("/api/v1/agents", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Compliance Auditor"
    assert data["require_approval"] is True
    assert sorted(data["tools"]) == ["Access Control Analyzer", "Compliance Check"]
    assert data["knowledge_source_ids"] == [ks1_id]
    assert data["owner"] == "Alpha Lead"


@pytest.mark.anyio
async def test_create_agent_nonexistent_org(client: TestClient, setup_tenants):
    random_org_id = str(uuid.uuid4())
    payload = {
        "organization_id": random_org_id,
        "name": "Ghost Agent",
        "description": "Should fail",
        "domain": "Operations",
        "system_instructions": "N/A",
    }
    res = client.post("/api/v1/agents", json=payload)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


@pytest.mark.anyio
async def test_create_agent_nonexistent_creator(client: TestClient, setup_tenants):
    org_id = setup_tenants["org1_id"]
    random_user_id = str(uuid.uuid4())
    payload = {
        "organization_id": org_id,
        "created_by_user_id": random_user_id,
        "name": "Ghost Creator Agent",
        "description": "Should fail",
        "domain": "Operations",
        "system_instructions": "N/A",
    }
    res = client.post("/api/v1/agents", json=payload)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


@pytest.mark.anyio
async def test_create_agent_cross_org_initial_knowledge_source(client: TestClient, setup_tenants):
    org1_id = setup_tenants["org1_id"]
    ks2_id = setup_tenants["ks2_id"]  # Belongs to Org 2

    payload = {
        "organization_id": org1_id,
        "name": "Cross Tenant Agent",
        "description": "Attempts to steal Org 2 knowledge",
        "domain": "Security",
        "system_instructions": "Audit",
        "knowledge_source_ids": [ks2_id],
    }
    res = client.post("/api/v1/agents", json=payload)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


@pytest.mark.anyio
async def test_create_agent_validation_errors(client: TestClient, setup_tenants):
    org_id = setup_tenants["org1_id"]

    # Empty name
    res = client.post("/api/v1/agents", json={
        "organization_id": org_id,
        "name": "   ",
        "description": "Valid description",
        "domain": "Operations",
        "system_instructions": "Valid instructions",
    })
    assert res.status_code == 422

    # Empty instructions
    res = client.post("/api/v1/agents", json={
        "organization_id": org_id,
        "name": "Valid Name",
        "description": "Valid description",
        "domain": "Operations",
        "system_instructions": "   ",
    })
    assert res.status_code == 422

    # Invalid status
    res = client.post("/api/v1/agents", json={
        "organization_id": org_id,
        "name": "Valid Name",
        "description": "Valid description",
        "domain": "Operations",
        "status": "Archived",
        "system_instructions": "Valid instructions",
    })
    assert res.status_code == 422


@pytest.mark.anyio
async def test_list_agents_filtering_and_pagination(client: TestClient, setup_tenants):
    org1_id = setup_tenants["org1_id"]
    org2_id = setup_tenants["org2_id"]

    # Create 2 agents in Org 1
    client.post("/api/v1/agents", json={
        "organization_id": org1_id,
        "name": "Alpha Agent 1",
        "description": "Desc",
        "domain": "Research",
        "status": "Active",
        "system_instructions": "Prompt",
    })
    client.post("/api/v1/agents", json={
        "organization_id": org1_id,
        "name": "Alpha Agent 2",
        "description": "Desc",
        "domain": "Operations",
        "status": "Paused",
        "system_instructions": "Prompt",
    })

    # Create 1 agent in Org 2
    client.post("/api/v1/agents", json={
        "organization_id": org2_id,
        "name": "Beta Agent 1",
        "description": "Desc",
        "domain": "Research",
        "status": "Active",
        "system_instructions": "Prompt",
    })

    # Filter by Org 1
    res = client.get(f"/api/v1/agents?organization_id={org1_id}")
    assert res.status_code == 200
    agents_org1 = res.json()
    assert len(agents_org1) == 2
    assert all(a["organization_id"] == org1_id for a in agents_org1)

    # Filter by domain in Org 1
    res_domain = client.get(f"/api/v1/agents?organization_id={org1_id}&domain=Research")
    assert res_domain.status_code == 200
    assert len(res_domain.json()) == 1
    assert res_domain.json()[0]["name"] == "Alpha Agent 1"

    # Filter by status in Org 1
    res_status = client.get(f"/api/v1/agents?organization_id={org1_id}&status=paused")
    assert res_status.status_code == 200
    assert len(res_status.json()) == 1
    assert res_status.json()[0]["name"] == "Alpha Agent 2"

    # Pagination: limit 1
    res_page = client.get(f"/api/v1/agents?organization_id={org1_id}&limit=1")
    assert res_page.status_code == 200
    assert len(res_page.json()) == 1

    # Filter with nonexistent org
    res_bad_org = client.get(f"/api/v1/agents?organization_id={uuid.uuid4()}")
    assert res_bad_org.status_code == 404


@pytest.mark.anyio
async def test_get_agent_and_tenant_isolation(client: TestClient, setup_tenants):
    org1_id = setup_tenants["org1_id"]
    org2_id = setup_tenants["org2_id"]

    agent_res = client.post("/api/v1/agents", json={
        "organization_id": org1_id,
        "name": "Triage Agent",
        "description": "Incident Triage",
        "domain": "Operations",
        "system_instructions": "Diagnose",
    })
    agent_id = agent_res.json()["id"]

    # Same organization lookup succeeds
    res = client.get(f"/api/v1/agents/{agent_id}?organization_id={org1_id}")
    assert res.status_code == 200
    assert res.json()["id"] == agent_id

    # Cross-organization lookup returns 404
    res_cross = client.get(f"/api/v1/agents/{agent_id}?organization_id={org2_id}")
    assert res_cross.status_code == 404
    assert "not found" in res_cross.json()["detail"].lower()

    # Non-existent ID returns 404
    res_none = client.get(f"/api/v1/agents/{uuid.uuid4()}")
    assert res_none.status_code == 404


@pytest.mark.anyio
async def test_update_agent_and_toggle_status(client: TestClient, setup_tenants):
    org1_id = setup_tenants["org1_id"]
    org2_id = setup_tenants["org2_id"]

    agent_res = client.post("/api/v1/agents", json={
        "organization_id": org1_id,
        "name": "HR Assistant",
        "description": "HR queries",
        "domain": "Human Resources",
        "status": "Active",
        "system_instructions": "Help employees",
        "require_approval": False,
    })
    agent_id = agent_res.json()["id"]

    # Update name, status to Paused, require_approval to True
    patch_res = client.patch(
        f"/api/v1/agents/{agent_id}?organization_id={org1_id}",
        json={
            "name": "HR Senior Intelligence",
            "status": "Paused",
            "require_approval": True,
        },
    )
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["name"] == "HR Senior Intelligence"
    assert updated["status"] == "Paused"
    assert updated["require_approval"] is True

    # Cross-organization update returns 404
    res_cross = client.patch(
        f"/api/v1/agents/{agent_id}?organization_id={org2_id}",
        json={"name": "Malicious Update"},
    )
    assert res_cross.status_code == 404

    # Validation: empty name returns 422
    bad_res = client.patch(
        f"/api/v1/agents/{agent_id}",
        json={"name": "   "},
    )
    assert bad_res.status_code == 422


@pytest.mark.anyio
async def test_delete_agent_and_tenant_isolation(client: TestClient, setup_tenants):
    org1_id = setup_tenants["org1_id"]
    org2_id = setup_tenants["org2_id"]

    agent_res = client.post("/api/v1/agents", json={
        "organization_id": org1_id,
        "name": "Disposable Agent",
        "description": "To be deleted",
        "domain": "Research",
        "system_instructions": "Temp",
    })
    agent_id = agent_res.json()["id"]

    # Cross-org delete returns 404
    cross_del = client.delete(f"/api/v1/agents/{agent_id}?organization_id={org2_id}")
    assert cross_del.status_code == 404

    # Valid delete returns 204
    del_res = client.delete(f"/api/v1/agents/{agent_id}?organization_id={org1_id}")
    assert del_res.status_code == 204

    # Subsequent get returns 404
    assert client.get(f"/api/v1/agents/{agent_id}").status_code == 404


# ==========================================
# Tool Relationship Tests
# ==========================================

@pytest.mark.anyio
async def test_tool_management_lifecycle(client: TestClient, setup_tenants):
    org1_id = setup_tenants["org1_id"]
    org2_id = setup_tenants["org2_id"]

    agent_res = client.post("/api/v1/agents", json={
        "organization_id": org1_id,
        "name": "Tool Worker",
        "description": "Tool testing",
        "domain": "Data Analytics",
        "system_instructions": "Analyze",
    })
    agent_id = agent_res.json()["id"]

    # Initially no tools
    res = client.get(f"/api/v1/agents/{agent_id}/tools")
    assert res.status_code == 200
    assert res.json() == []

    # Attach tool 1
    res_tool1 = client.post(
        f"/api/v1/agents/{agent_id}/tools?organization_id={org1_id}",
        json={"tool_name": "SQL Query Tool"},
    )
    assert res_tool1.status_code == 201
    assert res_tool1.json()["tool_name"] == "SQL Query Tool"

    # Attach tool 2
    res_tool2 = client.post(
        f"/api/v1/agents/{agent_id}/tools?organization_id={org1_id}",
        json={"tool_name": "Chart Generator"},
    )
    assert res_tool2.status_code == 201

    # Attach duplicate tool (idempotent)
    res_dup = client.post(
        f"/api/v1/agents/{agent_id}/tools?organization_id={org1_id}",
        json={"tool_name": "SQL Query Tool"},
    )
    assert res_dup.status_code == 201

    # List tools
    tools_list = client.get(f"/api/v1/agents/{agent_id}/tools").json()
    assert sorted(tools_list) == ["Chart Generator", "SQL Query Tool"]

    # Detach tool
    del_tool = client.delete(f"/api/v1/agents/{agent_id}/tools/SQL%20Query%20Tool?organization_id={org1_id}")
    assert del_tool.status_code == 204

    # List after detachment
    tools_after = client.get(f"/api/v1/agents/{agent_id}/tools").json()
    assert tools_after == ["Chart Generator"]

    # Detach unattached tool returns 404
    bad_detach = client.delete(f"/api/v1/agents/{agent_id}/tools/NonexistentTool")
    assert bad_detach.status_code == 404

    # Cross-organization tool attach returns 404
    cross_attach = client.post(
        f"/api/v1/agents/{agent_id}/tools?organization_id={org2_id}",
        json={"tool_name": "Intruder Tool"},
    )
    assert cross_attach.status_code == 404


# ==========================================
# Knowledge Source Relationship Tests
# ==========================================

@pytest.mark.anyio
async def test_knowledge_source_lifecycle_and_cross_org_rejection(client: TestClient, setup_tenants):
    org1_id = setup_tenants["org1_id"]
    ks1_id = setup_tenants["ks1_id"]
    org2_id = setup_tenants["org2_id"]
    ks2_id = setup_tenants["ks2_id"]

    agent_res = client.post("/api/v1/agents", json={
        "organization_id": org1_id,
        "name": "Knowledge Worker",
        "description": "Knowledge test",
        "domain": "Research",
        "system_instructions": "Read",
    })
    agent_id = agent_res.json()["id"]

    # Attach valid same-org KS
    attach_res = client.post(
        f"/api/v1/agents/{agent_id}/knowledge-sources?organization_id={org1_id}",
        json={"source_id": ks1_id},
    )
    assert attach_res.status_code == 201
    assert attach_res.json()["id"] == ks1_id

    # Cross-org KS attachment rejected (ks2 belongs to org2)
    bad_attach = client.post(
        f"/api/v1/agents/{agent_id}/knowledge-sources?organization_id={org1_id}",
        json={"source_id": ks2_id},
    )
    assert bad_attach.status_code == 404
    assert "not found" in bad_attach.json()["detail"].lower()

    # List agent knowledge sources
    list_ks = client.get(f"/api/v1/agents/{agent_id}/knowledge-sources?organization_id={org1_id}")
    assert list_ks.status_code == 200
    assert len(list_ks.json()) == 1
    assert list_ks.json()[0]["id"] == ks1_id

    # Detach knowledge source
    detach_res = client.delete(
        f"/api/v1/agents/{agent_id}/knowledge-sources/{ks1_id}?organization_id={org1_id}"
    )
    assert detach_res.status_code == 204

    # List after detachment
    list_empty = client.get(f"/api/v1/agents/{agent_id}/knowledge-sources")
    assert list_empty.json() == []

    # Detach unattached returns 404
    assert client.delete(f"/api/v1/agents/{agent_id}/knowledge-sources/{ks1_id}").status_code == 404


# ==========================================
# Cascade Behavior Tests
# ==========================================

@pytest.mark.anyio
async def test_agent_deletion_cascades_tools_and_knowledge_mappings(client: TestClient, setup_tenants):
    org1_id = setup_tenants["org1_id"]
    ks1_id = setup_tenants["ks1_id"]

    agent_res = client.post("/api/v1/agents", json={
        "organization_id": org1_id,
        "name": "Cascade Test Agent",
        "description": "Will be deleted",
        "domain": "Security",
        "system_instructions": "N/A",
        "tools": ["Vulnerability Audit"],
        "knowledge_source_ids": [ks1_id],
    })
    agent_id = agent_res.json()["id"]

    # Delete agent
    del_res = client.delete(f"/api/v1/agents/{agent_id}")
    assert del_res.status_code == 204

    # Ensure Knowledge Source still exists
    ks_res = client.get(f"/api/v1/knowledge/sources/{ks1_id}")
    assert ks_res.status_code == 200


@pytest.mark.anyio
async def test_knowledge_source_deletion_cascades_junction_entry(client: TestClient, setup_tenants):
    org1_id = setup_tenants["org1_id"]

    # Create dedicated knowledge source to delete
    ks_temp = client.post("/api/v1/knowledge/sources", json={"organization_id": org1_id, "name": "Ephemeral Docs"}).json()
    ks_temp_id = ks_temp["id"]

    agent_res = client.post("/api/v1/agents", json={
        "organization_id": org1_id,
        "name": "Persistent Agent",
        "description": "Stays alive",
        "domain": "Research",
        "system_instructions": "Prompt",
        "knowledge_source_ids": [ks_temp_id],
    })
    agent_id = agent_res.json()["id"]

    # Delete Knowledge Source
    del_ks = client.delete(f"/api/v1/knowledge/sources/{ks_temp_id}")
    assert del_ks.status_code == 204

    # Agent still exists, but attached knowledge sources is empty
    agent_check = client.get(f"/api/v1/agents/{agent_id}")
    assert agent_check.status_code == 200
    assert agent_check.json()["knowledge_source_ids"] == []


@pytest.mark.anyio
async def test_cross_org_tool_and_knowledge_list_isolation(client: TestClient, setup_tenants):
    org1_id = setup_tenants["org1_id"]
    org2_id = setup_tenants["org2_id"]

    agent_res = client.post("/api/v1/agents", json={
        "organization_id": org1_id,
        "name": "Isolation Agent",
        "description": "Tenant isolation check",
        "domain": "Security",
        "system_instructions": "Prompt",
    })
    agent_id = agent_res.json()["id"]

    # Cross-org list tools returns 404
    assert client.get(f"/api/v1/agents/{agent_id}/tools?organization_id={org2_id}").status_code == 404

    # Cross-org list knowledge-sources returns 404
    assert client.get(f"/api/v1/agents/{agent_id}/knowledge-sources?organization_id={org2_id}").status_code == 404


@pytest.mark.anyio
async def test_cross_org_tool_and_knowledge_detach_isolation(client: TestClient, setup_tenants):
    org1_id = setup_tenants["org1_id"]
    org2_id = setup_tenants["org2_id"]
    ks1_id = setup_tenants["ks1_id"]

    agent_res = client.post("/api/v1/agents", json={
        "organization_id": org1_id,
        "name": "Detach Isolation Agent",
        "description": "Detach isolation check",
        "domain": "Operations",
        "system_instructions": "Prompt",
        "tools": ["System Health Check"],
        "knowledge_source_ids": [ks1_id],
    })
    agent_id = agent_res.json()["id"]

    # Cross-org detach tool returns 404
    assert client.delete(
        f"/api/v1/agents/{agent_id}/tools/System%20Health%20Check?organization_id={org2_id}"
    ).status_code == 404

    # Cross-org detach knowledge source returns 404
    assert client.delete(
        f"/api/v1/agents/{agent_id}/knowledge-sources/{ks1_id}?organization_id={org2_id}"
    ).status_code == 404


@pytest.mark.anyio
async def test_tool_validation_blank_name(client: TestClient, setup_tenants):
    org1_id = setup_tenants["org1_id"]

    agent_res = client.post("/api/v1/agents", json={
        "organization_id": org1_id,
        "name": "Tool Blank Test Agent",
        "description": "Validation check",
        "domain": "Operations",
        "system_instructions": "Prompt",
    })
    agent_id = agent_res.json()["id"]

    # Blank tool name returns 422
    bad_res = client.post(
        f"/api/v1/agents/{agent_id}/tools",
        json={"tool_name": "   "},
    )
    assert bad_res.status_code == 422


@pytest.mark.anyio
async def test_duplicate_knowledge_source_attach(client: TestClient, setup_tenants):
    org1_id = setup_tenants["org1_id"]
    ks1_id = setup_tenants["ks1_id"]

    agent_res = client.post("/api/v1/agents", json={
        "organization_id": org1_id,
        "name": "Duplicate KS Agent",
        "description": "Idempotent attach check",
        "domain": "Research",
        "system_instructions": "Prompt",
        "knowledge_source_ids": [ks1_id],
    })
    agent_id = agent_res.json()["id"]

    # Re-attach same KS returns 201 without duplicating or erroring
    re_attach = client.post(
        f"/api/v1/agents/{agent_id}/knowledge-sources",
        json={"source_id": ks1_id},
    )
    assert re_attach.status_code == 201

    # List should still have exactly 1
    sources = client.get(f"/api/v1/agents/{agent_id}/knowledge-sources").json()
    assert len(sources) == 1


@pytest.mark.anyio
async def test_update_agent_domain_and_instructions(client: TestClient, setup_tenants):
    org1_id = setup_tenants["org1_id"]

    agent_res = client.post("/api/v1/agents", json={
        "organization_id": org1_id,
        "name": "Configurable Agent",
        "description": "Original description",
        "domain": "Research",
        "system_instructions": "Original instructions",
    })
    agent_id = agent_res.json()["id"]

    patch_res = client.patch(
        f"/api/v1/agents/{agent_id}",
        json={
            "description": "Updated description",
            "domain": "Data Analytics",
            "system_instructions": "Updated instructions",
        },
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["description"] == "Updated description"
    assert data["domain"] == "Data Analytics"
    assert data["system_instructions"] == "Updated instructions"


@pytest.mark.anyio
async def test_list_all_agents_unfiltered(client: TestClient, setup_tenants):
    org1_id = setup_tenants["org1_id"]
    org2_id = setup_tenants["org2_id"]

    client.post("/api/v1/agents", json={
        "organization_id": org1_id,
        "name": "Global List 1",
        "description": "Desc",
        "domain": "Security",
        "system_instructions": "Prompt",
    })
    client.post("/api/v1/agents", json={
        "organization_id": org2_id,
        "name": "Global List 2",
        "description": "Desc",
        "domain": "Human Resources",
        "system_instructions": "Prompt",
    })

    res = client.get("/api/v1/agents")
    assert res.status_code == 200
    all_agents = res.json()
    assert len(all_agents) >= 2

