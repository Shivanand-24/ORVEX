import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import Workflow, WorkflowStep, WorkflowExecution
from app.models.agent_execution import AgentExecution
from app.models.audit import AuditLog
from app.workflows.dag import WorkflowGraphValidator, DAGValidationError, MAX_WORKFLOW_STEPS


@pytest.fixture
def setup_workflow_data(client: TestClient):
    # Org 1 with Admin and Member
    org1_res = client.post("/api/v1/organizations", json={"name": "Alpha Corp", "slug": "alpha-corp"})
    org1_id = org1_res.json()["id"]

    user1_res = client.post("/api/v1/users", json={"email": "alpha_admin@alpha.com", "full_name": "Alpha Admin"})
    user1_id = user1_res.json()["id"]
    client.post(f"/api/v1/organizations/{org1_id}/members", json={"user_id": user1_id, "role": "admin"})

    user2_res = client.post("/api/v1/users", json={"email": "alpha_member@alpha.com", "full_name": "Alpha Member"})
    user2_id = user2_res.json()["id"]
    client.post(f"/api/v1/organizations/{org1_id}/members", json={"user_id": user2_id, "role": "member"})

    # Knowledge Source in Org 1
    ks1_res = client.post(
        "/api/v1/knowledge/sources",
        json={"organization_id": org1_id, "name": "Alpha Docs", "description": "Docs"},
    )
    ks1_id = ks1_res.json()["id"]

    # Agent in Org 1
    agent1_res = client.post(
        "/api/v1/agents",
        json={
            "organization_id": org1_id,
            "created_by_user_id": user1_id,
            "name": "Alpha Support Agent",
            "description": "Triage agent",
            "domain": "Customer Support",
            "status": "Active",
            "system_instructions": "Answer support questions",
            "require_approval": False,
        },
    )
    agent1_id = agent1_res.json()["id"]

    # Org 2 with Admin
    org2_res = client.post("/api/v1/organizations", json={"name": "Beta Inc", "slug": "beta-inc"})
    org2_id = org2_res.json()["id"]

    user3_res = client.post("/api/v1/users", json={"email": "beta_admin@beta.com", "full_name": "Beta Admin"})
    user3_id = user3_res.json()["id"]
    client.post(f"/api/v1/organizations/{org2_id}/members", json={"user_id": user3_id, "role": "admin"})

    # Knowledge Source in Org 2
    ks2_res = client.post(
        "/api/v1/knowledge/sources",
        json={"organization_id": org2_id, "name": "Beta Docs", "description": "Docs"},
    )
    ks2_id = ks2_res.json()["id"]

    # Agent in Org 2
    agent2_res = client.post(
        "/api/v1/agents",
        json={
            "organization_id": org2_id,
            "created_by_user_id": user3_id,
            "name": "Beta Research Agent",
            "description": "Research agent",
            "domain": "Research",
            "status": "Active",
            "system_instructions": "Conduct research",
            "require_approval": False,
        },
    )
    agent2_id = agent2_res.json()["id"]

    return {
        "org1_id": org1_id,
        "user1_id": user1_id,
        "user2_id": user2_id,
        "ks1_id": ks1_id,
        "agent1_id": agent1_id,
        "org2_id": org2_id,
        "user3_id": user3_id,
        "ks2_id": ks2_id,
        "agent2_id": agent2_id,
    }


# ====================================================================
# 1. DAG Validation Unit & API Tests
# ====================================================================

def test_dag_validator_valid_pipeline():
    steps = [
        {"step_id": "trigger", "step_type": "trigger", "next_step_ids": ["step1"]},
        {"step_id": "step1", "step_type": "agent", "next_step_ids": ["step2"]},
        {"step_id": "step2", "step_type": "action", "next_step_ids": []},
    ]
    WorkflowGraphValidator.validate(steps)


def test_dag_validator_cycle_detection():
    steps = [
        {"step_id": "trigger", "step_type": "trigger", "next_step_ids": ["step1"]},
        {"step_id": "step1", "step_type": "agent", "next_step_ids": ["step2"]},
        {"step_id": "step2", "step_type": "action", "next_step_ids": ["step1"]},
    ]
    with pytest.raises(DAGValidationError) as exc:
        WorkflowGraphValidator.validate(steps)
    assert "cycle" in str(exc.value).lower()


def test_dag_validator_self_reference():
    steps = [
        {"step_id": "trigger", "step_type": "trigger", "next_step_ids": ["trigger"]},
    ]
    with pytest.raises(DAGValidationError) as exc:
        WorkflowGraphValidator.validate(steps)
    assert "self" in str(exc.value).lower()


def test_dag_validator_missing_next_step():
    steps = [
        {"step_id": "trigger", "step_type": "trigger", "next_step_ids": ["non_existent"]},
    ]
    with pytest.raises(DAGValidationError) as exc:
        WorkflowGraphValidator.validate(steps)
    assert "non-existent" in str(exc.value).lower()


def test_dag_validator_duplicate_edges():
    steps = [
        {"step_id": "trigger", "step_type": "trigger", "next_step_ids": ["step1", "step1"]},
        {"step_id": "step1", "step_type": "agent", "next_step_ids": []},
    ]
    with pytest.raises(DAGValidationError) as exc:
        WorkflowGraphValidator.validate(steps)
    assert "duplicate edge" in str(exc.value).lower()


def test_dag_validator_no_trigger_root():
    steps = [
        {"step_id": "step1", "step_type": "agent", "next_step_ids": ["step2"]},
        {"step_id": "step2", "step_type": "action", "next_step_ids": []},
    ]
    with pytest.raises(DAGValidationError) as exc:
        WorkflowGraphValidator.validate(steps)
    assert "trigger" in str(exc.value).lower()


def test_dag_validator_multiple_roots():
    steps = [
        {"step_id": "trigger1", "step_type": "trigger", "next_step_ids": []},
        {"step_id": "trigger2", "step_type": "trigger", "next_step_ids": []},
    ]
    with pytest.raises(DAGValidationError) as exc:
        WorkflowGraphValidator.validate(steps)
    assert "root" in str(exc.value).lower()


def test_dag_validator_orphan_unreachable_step():
    steps = [
        {"step_id": "trigger", "step_type": "trigger", "next_step_ids": ["step1"]},
        {"step_id": "step1", "step_type": "agent", "next_step_ids": []},
        {"step_id": "orphan", "step_type": "action", "next_step_ids": []},
    ]
    with pytest.raises(DAGValidationError):
        WorkflowGraphValidator.validate(steps)


def test_dag_validator_max_steps_exceeded():
    steps = [{"step_id": "trigger", "step_type": "trigger", "next_step_ids": ["step1"]}]
    for i in range(1, MAX_WORKFLOW_STEPS + 2):
        next_ids = [f"step{i+1}"] if i < MAX_WORKFLOW_STEPS + 1 else []
        steps.append({"step_id": f"step{i}", "step_type": "agent", "next_step_ids": next_ids})
    with pytest.raises(DAGValidationError) as exc:
        WorkflowGraphValidator.validate(steps)
    assert "exceeds maximum" in str(exc.value).lower()


def test_dag_validator_invalid_step_id():
    steps = [
        {"step_id": "invalid id with spaces", "step_type": "trigger", "next_step_ids": []},
    ]
    with pytest.raises(DAGValidationError) as exc:
        WorkflowGraphValidator.validate(steps)
    assert "alphanumeric" in str(exc.value).lower()


# ====================================================================
# 2. Workflow CRUD Tests
# ====================================================================

@pytest.mark.anyio
async def test_create_workflow_minimal(client: TestClient, setup_workflow_data):
    org_id = setup_workflow_data["org1_id"]
    user_id = setup_workflow_data["user1_id"]

    res = client.post(
        "/api/v1/workflows",
        json={
            "organization_id": org_id,
            "created_by_user_id": user_id,
            "name": "Minimal Pipeline",
            "description": "Workflow with no initial steps",
            "status": "Draft",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Minimal Pipeline"
    assert data["status"] == "Draft"
    assert data["steps"] == []


@pytest.mark.anyio
async def test_create_workflow_with_valid_steps(client: TestClient, setup_workflow_data):
    org_id = setup_workflow_data["org1_id"]
    user_id = setup_workflow_data["user1_id"]
    agent_id = setup_workflow_data["agent1_id"]
    ks_id = setup_workflow_data["ks1_id"]

    res = client.post(
        "/api/v1/workflows",
        json={
            "organization_id": org_id,
            "created_by_user_id": user_id,
            "name": "Customer Support Escalation",
            "description": "Full valid workflow",
            "status": "Active",
            "steps": [
                {
                    "step_id": "trigger_step",
                    "title": "Ticket Trigger",
                    "type": "Trigger",
                    "config": {"trigger_event": "ticket.created"},
                    "next_step_ids": ["retrieval_step"],
                },
                {
                    "step_id": "retrieval_step",
                    "title": "Search KB",
                    "type": "Knowledge Retrieval",
                    "config": {"knowledge_source_id": ks_id, "query_template": "{{trigger.body}}"},
                    "next_step_ids": ["agent_step"],
                },
                {
                    "step_id": "agent_step",
                    "title": "Support Bot",
                    "type": "AI Agent",
                    "config": {"agent_id": agent_id},
                    "next_step_ids": [],
                },
            ],
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Customer Support Escalation"
    assert len(data["steps"]) == 3


@pytest.mark.anyio
async def test_create_workflow_invalid_dag_rejected(client: TestClient, setup_workflow_data):
    org_id = setup_workflow_data["org1_id"]
    user_id = setup_workflow_data["user1_id"]

    # Graph with cycle: trigger -> step1 -> trigger
    res = client.post(
        "/api/v1/workflows",
        json={
            "organization_id": org_id,
            "created_by_user_id": user_id,
            "name": "Cyclic Workflow",
            "status": "Draft",
            "steps": [
                {
                    "step_id": "trigger",
                    "title": "Trigger",
                    "type": "Trigger",
                    "config": {},
                    "next_step_ids": ["step1"],
                },
                {
                    "step_id": "step1",
                    "title": "Step 1",
                    "type": "Action",
                    "config": {},
                    "next_step_ids": ["trigger"],
                },
            ],
        },
    )
    assert res.status_code == 400
    assert "cycle" in res.json()["detail"].lower()


@pytest.mark.anyio
async def test_list_workflows_with_filtering_and_pagination(client: TestClient, setup_workflow_data):
    org_id = setup_workflow_data["org1_id"]
    user_id = setup_workflow_data["user1_id"]

    client.post(
        "/api/v1/workflows",
        json={"organization_id": org_id, "created_by_user_id": user_id, "name": "WF Draft 1", "description": "Desc", "status": "Draft"},
    )
    client.post(
        "/api/v1/workflows",
        json={"organization_id": org_id, "created_by_user_id": user_id, "name": "WF Active 1", "description": "Desc", "status": "Active"},
    )

    # Filter by org and status=Draft
    res = client.get(f"/api/v1/workflows?organization_id={org_id}&status=Draft")
    assert res.status_code == 200
    items = res.json()
    assert all(w["status"] == "Draft" for w in items)

    # Pagination
    res_page = client.get(f"/api/v1/workflows?organization_id={org_id}&limit=1&skip=0")
    assert res_page.status_code == 200
    assert len(res_page.json()) == 1


@pytest.mark.anyio
async def test_get_workflow_by_id(client: TestClient, setup_workflow_data):
    org_id = setup_workflow_data["org1_id"]
    user_id = setup_workflow_data["user1_id"]

    res = client.post(
        "/api/v1/workflows",
        json={"organization_id": org_id, "created_by_user_id": user_id, "name": "Get Target", "description": "Desc", "status": "Draft"},
    )
    wf_id = res.json()["id"]

    get_res = client.get(f"/api/v1/workflows/{wf_id}?organization_id={org_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == wf_id
    assert get_res.json()["name"] == "Get Target"


@pytest.mark.anyio
async def test_update_workflow_metadata(client: TestClient, setup_workflow_data):
    org_id = setup_workflow_data["org1_id"]
    user_id = setup_workflow_data["user1_id"]

    res = client.post(
        "/api/v1/workflows",
        json={"organization_id": org_id, "created_by_user_id": user_id, "name": "Initial Name", "description": "Initial Desc", "status": "Draft"},
    )
    wf_id = res.json()["id"]

    patch_res = client.patch(
        f"/api/v1/workflows/{wf_id}?organization_id={org_id}",
        json={"name": "Updated Name", "description": "Updated Description"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "Updated Name"
    assert patch_res.json()["description"] == "Updated Description"


@pytest.mark.anyio
async def test_toggle_workflow_status(client: TestClient, setup_workflow_data):
    org_id = setup_workflow_data["org1_id"]
    user_id = setup_workflow_data["user1_id"]

    res = client.post(
        "/api/v1/workflows",
        json={"organization_id": org_id, "created_by_user_id": user_id, "name": "Toggle WF", "description": "Desc", "status": "Draft"},
    )
    wf_id = res.json()["id"]

    # Toggle to active
    active_res = client.patch(
        f"/api/v1/workflows/{wf_id}/status?organization_id={org_id}",
        json={"status": "Active"},
    )
    assert active_res.status_code == 200
    assert active_res.json()["status"] == "Active"

    # Toggle to paused
    paused_res = client.patch(
        f"/api/v1/workflows/{wf_id}/status?organization_id={org_id}",
        json={"status": "Paused"},
    )
    assert paused_res.status_code == 200
    assert paused_res.json()["status"] == "Paused"

    # Invalid status returns 422
    inv_res = client.patch(
        f"/api/v1/workflows/{wf_id}/status?organization_id={org_id}",
        json={"status": "invalid_status"},
    )
    assert inv_res.status_code == 422


@pytest.mark.anyio
async def test_sync_workflow_steps(client: TestClient, setup_workflow_data):
    org_id = setup_workflow_data["org1_id"]
    user_id = setup_workflow_data["user1_id"]

    res = client.post(
        "/api/v1/workflows",
        json={"organization_id": org_id, "created_by_user_id": user_id, "name": "Sync Test", "description": "Desc", "status": "Draft"},
    )
    wf_id = res.json()["id"]

    # Sync steps with a valid DAG
    put_res = client.put(
        f"/api/v1/workflows/{wf_id}/steps?organization_id={org_id}",
        json={
            "steps": [
                {
                    "step_id": "trigger_node",
                    "title": "Trigger Node",
                    "type": "Trigger",
                    "config": {},
                    "next_step_ids": ["action_node"],
                },
                {
                    "step_id": "action_node",
                    "title": "Action Node",
                    "type": "Action",
                    "config": {"action_type": "send_notification"},
                    "next_step_ids": [],
                },
            ]
        },
    )
    assert put_res.status_code == 200
    assert len(put_res.json()["steps"]) == 2


@pytest.mark.anyio
async def test_delete_workflow_cascades(client: TestClient, setup_workflow_data, db_session: AsyncSession):
    org_id = setup_workflow_data["org1_id"]
    user_id = setup_workflow_data["user1_id"]

    res = client.post(
        "/api/v1/workflows",
        json={
            "organization_id": org_id,
            "created_by_user_id": user_id,
            "name": "Delete Target",
            "description": "Desc",
            "status": "Draft",
            "steps": [
                {"step_id": "trigger_1", "title": "Trigger", "type": "Trigger", "config": {}, "next_step_ids": []},
            ],
        },
    )
    wf_id = res.json()["id"]
    wf_uuid = uuid.UUID(wf_id)

    del_res = client.delete(f"/api/v1/workflows/{wf_id}?organization_id={org_id}")
    assert del_res.status_code == 204

    # Verify workflow and steps are gone
    wf = await db_session.get(Workflow, wf_uuid)
    assert wf is None
    steps = (await db_session.execute(select(WorkflowStep).where(WorkflowStep.workflow_id == wf_uuid))).scalars().all()
    assert len(steps) == 0


# ====================================================================
# 3. Tenant Isolation & Cross-Org Validation Tests
# ====================================================================

@pytest.mark.anyio
async def test_workflow_cross_org_access_404(client: TestClient, setup_workflow_data):
    org1_id = setup_workflow_data["org1_id"]
    org2_id = setup_workflow_data["org2_id"]
    user1_id = setup_workflow_data["user1_id"]

    # Create in Org 1
    res = client.post(
        "/api/v1/workflows",
        json={"organization_id": org1_id, "created_by_user_id": user1_id, "name": "Org 1 WF", "description": "Desc", "status": "Draft"},
    )
    wf_id = res.json()["id"]

    # Try to access with Org 2
    assert client.get(f"/api/v1/workflows/{wf_id}?organization_id={org2_id}").status_code == 404
    assert client.patch(f"/api/v1/workflows/{wf_id}?organization_id={org2_id}", json={"name": "Hack"}).status_code == 404
    assert client.delete(f"/api/v1/workflows/{wf_id}?organization_id={org2_id}").status_code == 404
    assert client.post(f"/api/v1/workflows/{wf_id}/execute", json={"organization_id": org2_id}).status_code == 404


@pytest.mark.anyio
async def test_workflow_create_with_cross_org_agent_fails(client: TestClient, setup_workflow_data):
    org1_id = setup_workflow_data["org1_id"]
    user1_id = setup_workflow_data["user1_id"]
    agent2_id = setup_workflow_data["agent2_id"]  # Belongs to Org 2

    res = client.post(
        "/api/v1/workflows",
        json={
            "organization_id": org1_id,
            "created_by_user_id": user1_id,
            "name": "Cross Org Agent WF",
            "description": "Desc",
            "status": "Draft",
            "steps": [
                {"step_id": "trigger_step", "title": "Trigger", "type": "Trigger", "config": {}, "next_step_ids": ["agent_step"]},
                {"step_id": "agent_step", "title": "Agent", "type": "AI Agent", "config": {"agent_id": agent2_id}, "next_step_ids": []},
            ],
        },
    )
    assert res.status_code == 404
    assert "agent" in res.json()["detail"].lower()


@pytest.mark.anyio
async def test_workflow_create_with_cross_org_knowledge_fails(client: TestClient, setup_workflow_data):
    org1_id = setup_workflow_data["org1_id"]
    user1_id = setup_workflow_data["user1_id"]
    ks2_id = setup_workflow_data["ks2_id"]  # Belongs to Org 2

    res = client.post(
        "/api/v1/workflows",
        json={
            "organization_id": org1_id,
            "created_by_user_id": user1_id,
            "name": "Cross Org KS WF",
            "description": "Desc",
            "status": "Draft",
            "steps": [
                {"step_id": "trigger_step", "title": "Trigger", "type": "Trigger", "config": {}, "next_step_ids": ["kb_step"]},
                {"step_id": "kb_step", "title": "KB", "type": "Knowledge Retrieval", "config": {"knowledge_source_id": ks2_id}, "next_step_ids": []},
            ],
        },
    )
    assert res.status_code == 404
    assert "knowledge source" in res.json()["detail"].lower()


# ====================================================================
# 4. Workflow Execution Lifecycle & Agent Delegation
# ====================================================================

@pytest.mark.anyio
async def test_execute_draft_workflow_rejected(client: TestClient, setup_workflow_data):
    org_id = setup_workflow_data["org1_id"]
    user_id = setup_workflow_data["user1_id"]

    res = client.post(
        "/api/v1/workflows",
        json={
            "organization_id": org_id,
            "created_by_user_id": user_id,
            "name": "Draft Execution Target",
            "description": "Desc",
            "status": "Draft",
            "steps": [
                {"step_id": "trigger", "title": "Trigger", "type": "Trigger", "config": {}, "next_step_ids": []},
            ],
        },
    )
    wf_id = res.json()["id"]

    exec_res = client.post(f"/api/v1/workflows/{wf_id}/execute", json={"organization_id": org_id})
    assert exec_res.status_code == 400
    assert "active" in exec_res.json()["detail"].lower()


@pytest.mark.anyio
async def test_execute_workflow_no_steps_rejected(client: TestClient, setup_workflow_data):
    org_id = setup_workflow_data["org1_id"]
    user_id = setup_workflow_data["user1_id"]

    res = client.post(
        "/api/v1/workflows",
        json={
            "organization_id": org_id,
            "created_by_user_id": user_id,
            "name": "Active but Empty",
            "description": "Desc",
            "status": "Active",
        },
    )
    wf_id = res.json()["id"]

    exec_res = client.post(f"/api/v1/workflows/{wf_id}/execute", json={"organization_id": org_id})
    assert exec_res.status_code == 400
    assert "configured steps" in exec_res.json()["detail"].lower()


@pytest.mark.anyio
async def test_execute_active_workflow_success(client: TestClient, setup_workflow_data):
    org_id = setup_workflow_data["org1_id"]
    user_id = setup_workflow_data["user1_id"]
    ks_id = setup_workflow_data["ks1_id"]
    agent_id = setup_workflow_data["agent1_id"]

    res = client.post(
        "/api/v1/workflows",
        json={
            "organization_id": org_id,
            "created_by_user_id": user_id,
            "name": "Live Pipeline",
            "description": "Desc",
            "status": "Active",
            "steps": [
                {"step_id": "trigger_1", "title": "Trigger Step", "type": "Trigger", "config": {}, "next_step_ids": ["retrieval_1"]},
                {"step_id": "retrieval_1", "title": "KB Search", "type": "Knowledge Retrieval", "config": {"knowledge_source_id": ks_id}, "next_step_ids": ["agent_1"]},
                {"step_id": "agent_1", "title": "Agent Bot", "type": "AI Agent", "config": {"agent_id": agent_id}, "next_step_ids": ["action_1"]},
                {"step_id": "action_1", "title": "Notification", "type": "Action", "config": {"action_type": "notify"}, "next_step_ids": []},
            ],
        },
    )
    wf_id = res.json()["id"]

    exec_res = client.post(
        f"/api/v1/workflows/{wf_id}/execute",
        json={"organization_id": org_id, "trigger_payload": {"ticket_id": 101}},
    )
    assert exec_res.status_code == 201
    exec_data = exec_res.json()
    assert exec_data["status"] == "completed"
    assert len(exec_data["execution_log"]) == 4
    step_titles_executed = [log["title"] for log in exec_data["execution_log"]]
    assert step_titles_executed == ["Trigger Step", "KB Search", "Agent Bot", "Notification"]


@pytest.mark.anyio
async def test_execute_workflow_delegates_to_agent_execution(client: TestClient, setup_workflow_data, db_session: AsyncSession):
    org_id = setup_workflow_data["org1_id"]
    user_id = setup_workflow_data["user1_id"]
    agent_id = setup_workflow_data["agent1_id"]

    res = client.post(
        "/api/v1/workflows",
        json={
            "organization_id": org_id,
            "created_by_user_id": user_id,
            "name": "Delegation Workflow",
            "description": "Desc",
            "status": "Active",
            "steps": [
                {"step_id": "trigger_step", "title": "Trigger", "type": "Trigger", "config": {}, "next_step_ids": ["agent_step"]},
                {"step_id": "agent_step", "title": "Agent Step", "type": "AI Agent", "config": {"agent_id": agent_id}, "next_step_ids": []},
            ],
        },
    )
    wf_id = res.json()["id"]

    exec_res = client.post(
        f"/api/v1/workflows/{wf_id}/execute",
        json={"organization_id": org_id},
    )
    assert exec_res.status_code == 201
    wf_exec_id = exec_res.json()["id"]

    # Check that an AgentExecution record was generated in the DB
    result = await db_session.execute(
        select(AgentExecution).where(AgentExecution.source_reference_id == uuid.UUID(wf_exec_id))
    )
    agent_exec = result.scalars().first()
    assert agent_exec is not None
    assert agent_exec.agent_id == uuid.UUID(agent_id)
    assert agent_exec.source == "workflow_step"
    assert agent_exec.status == "completed"


@pytest.mark.anyio
async def test_get_workflow_execution_by_id(client: TestClient, setup_workflow_data):
    org_id = setup_workflow_data["org1_id"]
    user_id = setup_workflow_data["user1_id"]

    wf_res = client.post(
        "/api/v1/workflows",
        json={
            "organization_id": org_id,
            "created_by_user_id": user_id,
            "name": "Execution Fetch WF",
            "description": "Desc",
            "status": "Active",
            "steps": [
                {"step_id": "trigger", "title": "Trigger", "type": "Trigger", "config": {}, "next_step_ids": []},
            ],
        },
    )
    wf_id = wf_res.json()["id"]

    exec_res = client.post(f"/api/v1/workflows/{wf_id}/execute", json={"organization_id": org_id})
    exec_id = exec_res.json()["id"]

    get_res = client.get(f"/api/v1/workflows/executions/{exec_id}?organization_id={org_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == exec_id
    assert get_res.json()["status"] == "completed"


@pytest.mark.anyio
async def test_get_workflow_execution_cross_org_404(client: TestClient, setup_workflow_data):
    org1_id = setup_workflow_data["org1_id"]
    org2_id = setup_workflow_data["org2_id"]
    user1_id = setup_workflow_data["user1_id"]

    wf_res = client.post(
        "/api/v1/workflows",
        json={
            "organization_id": org1_id,
            "created_by_user_id": user1_id,
            "name": "Isolation WF",
            "description": "Desc",
            "status": "Active",
            "steps": [
                {"step_id": "trigger", "title": "Trigger", "type": "Trigger", "config": {}, "next_step_ids": []},
            ],
        },
    )
    wf_id = wf_res.json()["id"]
    exec_res = client.post(f"/api/v1/workflows/{wf_id}/execute", json={"organization_id": org1_id})
    exec_id = exec_res.json()["id"]

    # Wrong org lookup
    assert client.get(f"/api/v1/workflows/executions/{exec_id}?organization_id={org2_id}").status_code == 404


# ====================================================================
# 5. Human-in-the-Loop Approval Tests
# ====================================================================

@pytest.mark.anyio
async def test_workflow_execution_pauses_for_approval(client: TestClient, setup_workflow_data):
    org_id = setup_workflow_data["org1_id"]
    user_id = setup_workflow_data["user1_id"]

    res = client.post(
        "/api/v1/workflows",
        json={
            "organization_id": org_id,
            "created_by_user_id": user_id,
            "name": "Approval Pipeline",
            "description": "Desc",
            "status": "Active",
            "steps": [
                {"step_id": "trigger", "title": "Trigger", "type": "Trigger", "config": {}, "next_step_ids": ["approval_gate"]},
                {"step_id": "approval_gate", "title": "Approval Gate", "type": "Human Approval", "config": {"approver_role": "admin"}, "next_step_ids": ["final_action"]},
                {"step_id": "final_action", "title": "Final Action", "type": "Action", "config": {"action_type": "post_message"}, "next_step_ids": []},
            ],
        },
    )
    wf_id = res.json()["id"]

    exec_res = client.post(f"/api/v1/workflows/{wf_id}/execute", json={"organization_id": org_id})
    assert exec_res.status_code == 201
    exec_data = exec_res.json()
    assert exec_data["status"] == "waiting_approval"

    # Verify execution_log records pause with resume_step_id
    last_log = exec_data["execution_log"][-1]
    assert last_log["title"] == "Approval Gate"
    assert last_log["status"] == "waiting_approval"
    assert last_log["resume_step_id"] is not None


@pytest.mark.anyio
async def test_workflow_approval_by_non_member_rejected(client: TestClient, setup_workflow_data):
    org1_id = setup_workflow_data["org1_id"]
    user1_id = setup_workflow_data["user1_id"]
    user3_id = setup_workflow_data["user3_id"]  # Member of Org 2, not Org 1

    res = client.post(
        "/api/v1/workflows",
        json={
            "organization_id": org1_id,
            "created_by_user_id": user1_id,
            "name": "Gate Check",
            "description": "Desc",
            "status": "Active",
            "steps": [
                {"step_id": "trigger", "title": "Trigger", "type": "Trigger", "config": {}, "next_step_ids": ["approval_step"]},
                {"step_id": "approval_step", "title": "Approval", "type": "Human Approval", "config": {}, "next_step_ids": []},
            ],
        },
    )
    wf_id = res.json()["id"]
    exec_res = client.post(f"/api/v1/workflows/{wf_id}/execute", json={"organization_id": org1_id})
    exec_id = exec_res.json()["id"]

    # Non-member attempts approval
    appr_res = client.post(
        f"/api/v1/workflows/executions/{exec_id}/approve?organization_id={org1_id}",
        json={"user_id": user3_id},
    )
    assert appr_res.status_code == 400
    assert "not an active member" in appr_res.json()["detail"].lower()


@pytest.mark.anyio
async def test_workflow_approval_resumes_to_completion(client: TestClient, setup_workflow_data):
    org_id = setup_workflow_data["org1_id"]
    user_id = setup_workflow_data["user1_id"]

    res = client.post(
        "/api/v1/workflows",
        json={
            "organization_id": org_id,
            "created_by_user_id": user_id,
            "name": "Resume Pipeline",
            "description": "Desc",
            "status": "Active",
            "steps": [
                {"step_id": "trigger", "title": "Trigger", "type": "Trigger", "config": {}, "next_step_ids": ["gate"]},
                {"step_id": "gate", "title": "Approval Gate", "type": "Human Approval", "config": {}, "next_step_ids": ["finish"]},
                {"step_id": "finish", "title": "Finish Action", "type": "Action", "config": {"action_type": "complete"}, "next_step_ids": []},
            ],
        },
    )
    wf_id = res.json()["id"]
    exec_res = client.post(f"/api/v1/workflows/{wf_id}/execute", json={"organization_id": org_id})
    exec_id = exec_res.json()["id"]
    assert exec_res.json()["status"] == "waiting_approval"

    # Approve with valid member
    appr_res = client.post(
        f"/api/v1/workflows/executions/{exec_id}/approve?organization_id={org_id}",
        json={"user_id": user_id},
    )
    assert appr_res.status_code == 200
    data = appr_res.json()
    assert data["status"] == "completed"
    # Verify execution finished all 3 steps
    executed_titles = [log["title"] for log in data["execution_log"]]
    assert "Finish Action" in executed_titles


@pytest.mark.anyio
async def test_repeated_approval_rejected(client: TestClient, setup_workflow_data):
    org_id = setup_workflow_data["org1_id"]
    user_id = setup_workflow_data["user1_id"]

    res = client.post(
        "/api/v1/workflows",
        json={
            "organization_id": org_id,
            "created_by_user_id": user_id,
            "name": "Repeated Approval Check",
            "description": "Desc",
            "status": "Active",
            "steps": [
                {"step_id": "trigger", "title": "Trigger", "type": "Trigger", "config": {}, "next_step_ids": ["gate"]},
                {"step_id": "gate", "title": "Gate", "type": "Human Approval", "config": {}, "next_step_ids": []},
            ],
        },
    )
    wf_id = res.json()["id"]
    exec_res = client.post(f"/api/v1/workflows/{wf_id}/execute", json={"organization_id": org_id})
    exec_id = exec_res.json()["id"]

    # First approval succeeds
    appr1 = client.post(
        f"/api/v1/workflows/executions/{exec_id}/approve?organization_id={org_id}",
        json={"user_id": user_id},
    )
    assert appr1.status_code == 200

    # Second approval rejected with 400
    appr2 = client.post(
        f"/api/v1/workflows/executions/{exec_id}/approve?organization_id={org_id}",
        json={"user_id": user_id},
    )
    assert appr2.status_code == 400
    assert "waiting_approval" in appr2.json()["detail"].lower()


# ====================================================================
# 6. Workflow Cancellation Tests
# ====================================================================

@pytest.mark.anyio
async def test_workflow_cancellation_waiting_approval(client: TestClient, setup_workflow_data):
    org_id = setup_workflow_data["org1_id"]
    user_id = setup_workflow_data["user1_id"]

    res = client.post(
        "/api/v1/workflows",
        json={
            "organization_id": org_id,
            "created_by_user_id": user_id,
            "name": "Cancel Target",
            "description": "Desc",
            "status": "Active",
            "steps": [
                {"step_id": "trigger", "title": "Trigger", "type": "Trigger", "config": {}, "next_step_ids": ["gate"]},
                {"step_id": "gate", "title": "Gate", "type": "Human Approval", "config": {}, "next_step_ids": []},
            ],
        },
    )
    wf_id = res.json()["id"]
    exec_res = client.post(f"/api/v1/workflows/{wf_id}/execute", json={"organization_id": org_id})
    exec_id = exec_res.json()["id"]

    cancel_res = client.post(
        f"/api/v1/workflows/executions/{exec_id}/cancel?organization_id={org_id}",
        json={"reason": "User requested abort"},
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"


@pytest.mark.anyio
async def test_workflow_cancellation_terminal_state_rejected(client: TestClient, setup_workflow_data):
    org_id = setup_workflow_data["org1_id"]
    user_id = setup_workflow_data["user1_id"]

    res = client.post(
        "/api/v1/workflows",
        json={
            "organization_id": org_id,
            "created_by_user_id": user_id,
            "name": "Terminal Cancel Check",
            "description": "Desc",
            "status": "Active",
            "steps": [
                {"step_id": "trigger", "title": "Trigger", "type": "Trigger", "config": {}, "next_step_ids": []},
            ],
        },
    )
    wf_id = res.json()["id"]
    exec_res = client.post(f"/api/v1/workflows/{wf_id}/execute", json={"organization_id": org_id})
    exec_id = exec_res.json()["id"]
    assert exec_res.json()["status"] == "completed"

    # Cancellation of completed execution rejected
    cancel_res = client.post(
        f"/api/v1/workflows/executions/{exec_id}/cancel?organization_id={org_id}",
        json={"reason": "Abort after completion"},
    )
    assert cancel_res.status_code == 400
    assert "terminal state" in cancel_res.json()["detail"].lower()


# ====================================================================
# 7. Privacy-safe Audit Logging Tests
# ====================================================================

@pytest.mark.anyio
async def test_workflow_execution_audit_logging_privacy(client: TestClient, setup_workflow_data, db_session: AsyncSession):
    org_id = setup_workflow_data["org1_id"]
    user_id = setup_workflow_data["user1_id"]

    res = client.post(
        "/api/v1/workflows",
        json={
            "organization_id": org_id,
            "created_by_user_id": user_id,
            "name": "Audit Tracked Pipeline",
            "description": "Desc",
            "status": "Active",
            "steps": [
                {"step_id": "trigger", "title": "Trigger", "type": "Trigger", "config": {}, "next_step_ids": ["gate"]},
                {"step_id": "gate", "title": "Gate", "type": "Human Approval", "config": {}, "next_step_ids": ["action"]},
                {"step_id": "action", "title": "Action", "type": "Action", "config": {"action_type": "do_task"}, "next_step_ids": []},
            ],
        },
    )
    wf_id = res.json()["id"]

    # 1. Trigger -> emits workflow.execution.triggered and workflow.execution.waiting_approval
    exec_res = client.post(
        f"/api/v1/workflows/{wf_id}/execute",
        json={"organization_id": org_id, "trigger_payload": {"secret_token": "super_secret_token_123"}},
    )
    exec_id = exec_res.json()["id"]

    # 2. Approve -> emits workflow.execution.approved and workflow.execution.completed
    client.post(
        f"/api/v1/workflows/executions/{exec_id}/approve?organization_id={org_id}",
        json={"user_id": user_id},
    )

    # Query audit logs for this execution
    result = await db_session.execute(
        select(AuditLog).where(AuditLog.resource_id == uuid.UUID(exec_id)).order_by(AuditLog.created_at.asc())
    )
    logs = list(result.scalars().all())
    actions = [log.action for log in logs]

    assert "workflow.execution.started" in actions
    assert any("approval" in a for a in actions)
    assert "workflow.execution.approved" in actions
    assert "workflow.execution.completed" in actions

    # Verify audit details DO NOT contain the secret token or raw trigger payload
    for log in logs:
        assert "super_secret_token_123" not in str(log.details)
