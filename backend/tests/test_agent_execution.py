import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.execution.lifecycle import (
    ExecutionStatus,
    InvalidStateTransitionError,
    validate_transition,
)
from app.execution.context import ExecutionContext
from app.execution.resolver import agent_resolver
from app.models.agent_execution import AgentExecution
from app.models.audit import AuditLog
from app.services.agent_execution_service import agent_execution_service


@pytest.fixture
def setup_data(client: TestClient):
    # Org 1 with User 1 (Admin), User 2 (Member)
    org1_res = client.post("/api/v1/organizations", json={"name": "Alpha Corp", "slug": "alpha-corp"})
    org1_id = org1_res.json()["id"]

    user1_res = client.post("/api/v1/users", json={"email": "alpha_admin@alpha.com", "full_name": "Alpha Admin"})
    user1_id = user1_res.json()["id"]
    client.post(f"/api/v1/organizations/{org1_id}/members", json={"user_id": user1_id, "role": "admin"})

    user2_res = client.post("/api/v1/users", json={"email": "alpha_analyst@alpha.com", "full_name": "Alpha Analyst"})
    user2_id = user2_res.json()["id"]
    client.post(f"/api/v1/organizations/{org1_id}/members", json={"user_id": user2_id, "role": "member"})

    # Org 2 with User 3 (Admin)
    org2_res = client.post("/api/v1/organizations", json={"name": "Beta Inc", "slug": "beta-inc"})
    org2_id = org2_res.json()["id"]

    user3_res = client.post("/api/v1/users", json={"email": "beta_admin@beta.com", "full_name": "Beta Admin"})
    user3_id = user3_res.json()["id"]
    client.post(f"/api/v1/organizations/{org2_id}/members", json={"user_id": user3_id, "role": "admin"})

    # Autonomous Agent in Org 1 (require_approval=False)
    agent1_res = client.post(
        "/api/v1/agents",
        json={
            "organization_id": org1_id,
            "created_by_user_id": user1_id,
            "name": "Data Analyzer",
            "description": "Analyzes metrics automatically.",
            "domain": "Analytics",
            "status": "Active",
            "system_instructions": "Process input tables.",
            "require_approval": False,
        },
    )
    agent1_id = agent1_res.json()["id"]

    # Governed Agent in Org 1 (require_approval=True)
    agent2_res = client.post(
        "/api/v1/agents",
        json={
            "organization_id": org1_id,
            "created_by_user_id": user1_id,
            "name": "Deployment Operator",
            "description": "Requires human approval for production.",
            "domain": "DevOps",
            "status": "Active",
            "system_instructions": "Prepare deploy commands.",
            "require_approval": True,
        },
    )
    agent2_id = agent2_res.json()["id"]

    # Paused Agent in Org 1
    agent3_res = client.post(
        "/api/v1/agents",
        json={
            "organization_id": org1_id,
            "created_by_user_id": user1_id,
            "name": "Paused Monitor",
            "description": "Currently paused.",
            "domain": "Monitoring",
            "status": "Paused",
            "system_instructions": "Watch alerts.",
            "require_approval": False,
        },
    )
    agent3_id = agent3_res.json()["id"]

    # Agent in Org 2
    agent_org2_res = client.post(
        "/api/v1/agents",
        json={
            "organization_id": org2_id,
            "created_by_user_id": user3_id,
            "name": "Beta Sentinel",
            "description": "Beta agent.",
            "domain": "Security",
            "status": "Active",
            "system_instructions": "Monitor Beta assets.",
            "require_approval": False,
        },
    )
    agent_org2_id = agent_org2_res.json()["id"]

    return {
        "org1_id": org1_id,
        "user1_id": user1_id,
        "user2_id": user2_id,
        "org2_id": org2_id,
        "user3_id": user3_id,
        "agent1_id": agent1_id,
        "agent2_id": agent2_id,
        "agent3_id": agent3_id,
        "agent_org2_id": agent_org2_id,
    }


# ==========================================
# 1. Domain Primitives & Lifecycle Tests
# ==========================================

def test_lifecycle_valid_transitions():
    assert validate_transition(ExecutionStatus.PENDING, ExecutionStatus.RUNNING) == ExecutionStatus.RUNNING
    assert validate_transition(ExecutionStatus.PENDING, ExecutionStatus.WAITING_FOR_APPROVAL) == ExecutionStatus.WAITING_FOR_APPROVAL
    assert validate_transition(ExecutionStatus.PENDING, ExecutionStatus.CANCELLED) == ExecutionStatus.CANCELLED
    assert validate_transition(ExecutionStatus.WAITING_FOR_APPROVAL, ExecutionStatus.RUNNING) == ExecutionStatus.RUNNING
    assert validate_transition(ExecutionStatus.WAITING_FOR_APPROVAL, ExecutionStatus.CANCELLED) == ExecutionStatus.CANCELLED
    assert validate_transition(ExecutionStatus.RUNNING, ExecutionStatus.COMPLETED) == ExecutionStatus.COMPLETED
    assert validate_transition(ExecutionStatus.RUNNING, ExecutionStatus.FAILED) == ExecutionStatus.FAILED
    assert validate_transition(ExecutionStatus.RUNNING, ExecutionStatus.CANCELLED) == ExecutionStatus.CANCELLED


def test_lifecycle_invalid_transitions():
    with pytest.raises(InvalidStateTransitionError):
        validate_transition(ExecutionStatus.COMPLETED, ExecutionStatus.RUNNING)

    with pytest.raises(InvalidStateTransitionError):
        validate_transition(ExecutionStatus.FAILED, ExecutionStatus.PENDING)

    with pytest.raises(InvalidStateTransitionError):
        validate_transition(ExecutionStatus.CANCELLED, ExecutionStatus.RUNNING)

    with pytest.raises(InvalidStateTransitionError):
        validate_transition(ExecutionStatus.PENDING, ExecutionStatus.COMPLETED)


def test_execution_context_instantiation():
    ctx = ExecutionContext(
        execution_id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        agent_id=uuid.uuid4(),
        input_prompt="Summarize documents",
        status=ExecutionStatus.RUNNING,
    )
    assert ctx.status == ExecutionStatus.RUNNING
    assert ctx.intermediate_tool_results == []
    ctx.add_tool_result({"action": "lookup", "target": "docs"})
    assert len(ctx.intermediate_tool_results) == 1
    assert ctx.intermediate_tool_results[0]["action"] == "lookup"



# ==========================================
# 2. Execution Creation API Tests
# ==========================================

@pytest.mark.anyio
async def test_trigger_execution_autonomous_agent(client: TestClient, setup_data):
    agent_id = setup_data["agent1_id"]
    org_id = setup_data["org1_id"]
    user_id = setup_data["user1_id"]

    payload = {
        "organization_id": org_id,
        "triggered_by_user_id": user_id,
        "source": "direct_api",
        "input_prompt": "Analyze Q3 financial report.",
    }
    res = client.post(f"/api/v1/agents/{agent_id}/executions", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["agent_id"] == agent_id
    assert data["organization_id"] == org_id
    assert data["triggered_by_user_id"] == user_id
    assert data["status"] == "running"
    assert data["require_approval"] is False
    assert data["approved_by_user_id"] is None
    assert data["source"] == "direct_api"
    assert data["input_prompt"] == "Analyze Q3 financial report."
    assert data["output_result"] is None
    assert data["tokens_used"] == 0
    assert data["latency_ms"] == 0
    assert data["started_at"] is not None
    assert data["completed_at"] is None


@pytest.mark.anyio
async def test_trigger_execution_approval_required(client: TestClient, setup_data):
    agent_id = setup_data["agent2_id"]
    org_id = setup_data["org1_id"]

    payload = {
        "organization_id": org_id,
        "source": "assistant_chat",
        "source_reference_id": str(uuid.uuid4()),
        "input_prompt": "Deploy hotfix to staging.",
    }
    res = client.post(f"/api/v1/agents/{agent_id}/executions", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["agent_id"] == agent_id
    assert data["status"] == "waiting_for_approval"
    assert data["require_approval"] is True
    assert data["source"] == "assistant_chat"
    assert data["source_reference_id"] == payload["source_reference_id"]


@pytest.mark.anyio
async def test_trigger_execution_paused_agent_rejected(client: TestClient, setup_data):
    agent_id = setup_data["agent3_id"]
    org_id = setup_data["org1_id"]

    payload = {
        "organization_id": org_id,
        "input_prompt": "Run check.",
    }
    res = client.post(f"/api/v1/agents/{agent_id}/executions", json=payload)
    assert res.status_code == 400
    assert "Paused" in res.json()["detail"]


@pytest.mark.anyio
async def test_trigger_execution_nonexistent_agent(client: TestClient, setup_data):
    fake_id = str(uuid.uuid4())
    payload = {
        "organization_id": setup_data["org1_id"],
        "input_prompt": "Run check.",
    }
    res = client.post(f"/api/v1/agents/{fake_id}/executions", json=payload)
    assert res.status_code == 404


@pytest.mark.anyio
async def test_trigger_execution_cross_org_tenant_isolation(client: TestClient, setup_data):
    # Agent 1 belongs to Org 1; user attempts to execute in Org 2
    agent_id = setup_data["agent1_id"]
    payload = {
        "organization_id": setup_data["org2_id"],
        "input_prompt": "Cross-tenant intrusion attempt.",
    }
    res = client.post(f"/api/v1/agents/{agent_id}/executions", json=payload)
    assert res.status_code == 404


@pytest.mark.anyio
async def test_trigger_execution_invalid_source_validation(client: TestClient, setup_data):
    agent_id = setup_data["agent1_id"]
    payload = {
        "organization_id": setup_data["org1_id"],
        "source": "unsupported_channel",
        "input_prompt": "Run test.",
    }
    res = client.post(f"/api/v1/agents/{agent_id}/executions", json=payload)
    assert res.status_code == 422


@pytest.mark.anyio
async def test_trigger_execution_blank_prompt_validation(client: TestClient, setup_data):
    agent_id = setup_data["agent1_id"]
    payload = {
        "organization_id": setup_data["org1_id"],
        "input_prompt": "   ",
    }
    res = client.post(f"/api/v1/agents/{agent_id}/executions", json=payload)
    assert res.status_code == 422


# ==========================================
# 3. Execution Retrieval & Filtering Tests
# ==========================================

@pytest.mark.anyio
async def test_get_execution_by_id(client: TestClient, setup_data):
    agent_id = setup_data["agent1_id"]
    org_id = setup_data["org1_id"]

    create_res = client.post(
        f"/api/v1/agents/{agent_id}/executions",
        json={"organization_id": org_id, "input_prompt": "Task 1"},
    )
    exec_id = create_res.json()["id"]

    get_res = client.get(f"/api/v1/executions/{exec_id}?organization_id={org_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == exec_id
    assert get_res.json()["input_prompt"] == "Task 1"


@pytest.mark.anyio
async def test_get_execution_cross_org_returns_404(client: TestClient, setup_data):
    agent_id = setup_data["agent1_id"]
    org1_id = setup_data["org1_id"]
    org2_id = setup_data["org2_id"]

    create_res = client.post(
        f"/api/v1/agents/{agent_id}/executions",
        json={"organization_id": org1_id, "input_prompt": "Org 1 Secret Task"},
    )
    exec_id = create_res.json()["id"]

    # Query with Org 2 ID -> 404
    get_res = client.get(f"/api/v1/executions/{exec_id}?organization_id={org2_id}")
    assert get_res.status_code == 404


@pytest.mark.anyio
async def test_list_executions_by_agent_and_filtering(client: TestClient, setup_data):
    agent1_id = setup_data["agent1_id"]
    agent2_id = setup_data["agent2_id"]
    org_id = setup_data["org1_id"]

    # Create 2 runs for agent 1 (running)
    client.post(f"/api/v1/agents/{agent1_id}/executions", json={"organization_id": org_id, "input_prompt": "Run 1"})
    client.post(f"/api/v1/agents/{agent1_id}/executions", json={"organization_id": org_id, "input_prompt": "Run 2"})

    # Create 1 run for agent 2 (waiting_for_approval)
    client.post(f"/api/v1/agents/{agent2_id}/executions", json={"organization_id": org_id, "input_prompt": "Run 3"})

    # List agent 1 runs
    list_res = client.get(f"/api/v1/agents/{agent1_id}/executions?organization_id={org_id}")
    assert list_res.status_code == 200
    runs = list_res.json()
    assert len(runs) == 2

    # Filter agent 1 runs by status
    filter_res = client.get(f"/api/v1/agents/{agent1_id}/executions?organization_id={org_id}&status=running")
    assert filter_res.status_code == 200
    assert len(filter_res.json()) == 2

    filter_waiting = client.get(f"/api/v1/agents/{agent1_id}/executions?organization_id={org_id}&status=waiting_for_approval")
    assert filter_waiting.status_code == 200
    assert len(filter_waiting.json()) == 0


@pytest.mark.anyio
async def test_list_executions_pagination(client: TestClient, setup_data):
    agent_id = setup_data["agent1_id"]
    org_id = setup_data["org1_id"]

    for i in range(5):
        client.post(f"/api/v1/agents/{agent_id}/executions", json={"organization_id": org_id, "input_prompt": f"Task {i}"})

    res_page1 = client.get(f"/api/v1/agents/{agent_id}/executions?organization_id={org_id}&skip=0&limit=2")
    assert res_page1.status_code == 200
    assert len(res_page1.json()) == 2

    res_page2 = client.get(f"/api/v1/agents/{agent_id}/executions?organization_id={org_id}&skip=2&limit=2")
    assert res_page2.status_code == 200
    assert len(res_page2.json()) == 2

    # Confirm different records
    ids1 = {r["id"] for r in res_page1.json()}
    ids2 = {r["id"] for r in res_page2.json()}
    assert ids1.isdisjoint(ids2)


# ==========================================
# 4. Approval Workflow Tests
# ==========================================

@pytest.mark.anyio
async def test_approve_execution_success(client: TestClient, setup_data):
    agent_id = setup_data["agent2_id"]  # require_approval=True
    org_id = setup_data["org1_id"]
    admin_id = setup_data["user1_id"]

    # Trigger execution
    create_res = client.post(
        f"/api/v1/agents/{agent_id}/executions",
        json={"organization_id": org_id, "input_prompt": "Deploy to prod."},
    )
    exec_id = create_res.json()["id"]
    assert create_res.json()["status"] == "waiting_for_approval"

    # Approve
    approve_res = client.post(
        f"/api/v1/executions/{exec_id}/approve?organization_id={org_id}",
        json={"user_id": admin_id},
    )
    assert approve_res.status_code == 200
    data = approve_res.json()
    assert data["status"] == "running"
    assert data["approved_by_user_id"] == admin_id


@pytest.mark.anyio
async def test_approve_execution_not_waiting_raises_400(client: TestClient, setup_data):
    agent_id = setup_data["agent1_id"]  # require_approval=False, directly "running"
    org_id = setup_data["org1_id"]
    admin_id = setup_data["user1_id"]

    create_res = client.post(
        f"/api/v1/agents/{agent_id}/executions",
        json={"organization_id": org_id, "input_prompt": "Direct run."},
    )
    exec_id = create_res.json()["id"]
    assert create_res.json()["status"] == "running"

    # Attempt to approve an already running execution
    approve_res = client.post(
        f"/api/v1/executions/{exec_id}/approve?organization_id={org_id}",
        json={"user_id": admin_id},
    )
    assert approve_res.status_code == 400
    assert "Invalid execution lifecycle transition" in approve_res.json()["detail"]



@pytest.mark.anyio
async def test_approve_execution_non_member_approver_raises_400(client: TestClient, setup_data):
    agent_id = setup_data["agent2_id"]
    org_id = setup_data["org1_id"]
    foreign_user_id = setup_data["user3_id"]  # User 3 belongs to Org 2

    create_res = client.post(
        f"/api/v1/agents/{agent_id}/executions",
        json={"organization_id": org_id, "input_prompt": "Deploy run."},
    )
    exec_id = create_res.json()["id"]

    # Approver is not a member of Org 1
    approve_res = client.post(
        f"/api/v1/executions/{exec_id}/approve?organization_id={org_id}",
        json={"user_id": foreign_user_id},
    )
    assert approve_res.status_code == 400
    assert "not a member" in approve_res.json()["detail"]


@pytest.mark.anyio
async def test_approve_execution_cross_org_returns_404(client: TestClient, setup_data):
    agent_id = setup_data["agent2_id"]
    org1_id = setup_data["org1_id"]
    org2_id = setup_data["org2_id"]
    admin_id = setup_data["user1_id"]

    create_res = client.post(
        f"/api/v1/agents/{agent_id}/executions",
        json={"organization_id": org1_id, "input_prompt": "Deploy run."},
    )
    exec_id = create_res.json()["id"]

    # Query with Org 2
    approve_res = client.post(
        f"/api/v1/executions/{exec_id}/approve?organization_id={org2_id}",
        json={"user_id": admin_id},
    )
    assert approve_res.status_code == 404


# ==========================================
# 5. Cancellation Workflow Tests
# ==========================================

@pytest.mark.anyio
async def test_cancel_execution_from_waiting_for_approval(client: TestClient, setup_data):
    agent_id = setup_data["agent2_id"]
    org_id = setup_data["org1_id"]
    user_id = setup_data["user1_id"]

    create_res = client.post(
        f"/api/v1/agents/{agent_id}/executions",
        json={"organization_id": org_id, "input_prompt": "Deploy run."},
    )
    exec_id = create_res.json()["id"]

    cancel_res = client.post(
        f"/api/v1/executions/{exec_id}/cancel?organization_id={org_id}",
        json={"user_id": user_id, "reason": "Operator rejected approval"},
    )
    assert cancel_res.status_code == 200
    data = cancel_res.json()
    assert data["status"] == "cancelled"
    assert data["completed_at"] is not None
    assert "Operator rejected approval" in data["error_message"]


@pytest.mark.anyio
async def test_cancel_execution_from_running(client: TestClient, setup_data):
    agent_id = setup_data["agent1_id"]
    org_id = setup_data["org1_id"]

    create_res = client.post(
        f"/api/v1/agents/{agent_id}/executions",
        json={"organization_id": org_id, "input_prompt": "Analyze dataset."},
    )
    exec_id = create_res.json()["id"]
    assert create_res.json()["status"] == "running"

    cancel_res = client.post(
        f"/api/v1/executions/{exec_id}/cancel?organization_id={org_id}",
        json={"reason": "User abort"},
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"


@pytest.mark.anyio
async def test_cancel_execution_already_cancelled_raises_400(client: TestClient, setup_data):
    agent_id = setup_data["agent1_id"]
    org_id = setup_data["org1_id"]

    create_res = client.post(
        f"/api/v1/agents/{agent_id}/executions",
        json={"organization_id": org_id, "input_prompt": "Analyze dataset."},
    )
    exec_id = create_res.json()["id"]

    # First cancel
    client.post(f"/api/v1/executions/{exec_id}/cancel?organization_id={org_id}", json={})

    # Second cancel -> 400
    cancel_res2 = client.post(f"/api/v1/executions/{exec_id}/cancel?organization_id={org_id}", json={})
    assert cancel_res2.status_code == 400


# ==========================================
# 6. Service Level Completion & Failure Tests
# ==========================================

@pytest.mark.anyio
async def test_service_complete_execution(client: TestClient, setup_data, db_session: AsyncSession):
    agent_id = setup_data["agent1_id"]
    org_id = setup_data["org1_id"]

    create_res = client.post(
        f"/api/v1/agents/{agent_id}/executions",
        json={"organization_id": org_id, "input_prompt": "Generate summary."},
    )
    exec_id = uuid.UUID(create_res.json()["id"])

    # Simulate runtime completion via service interface
    completed_exec = await agent_execution_service.complete_execution(
        db=db_session,
        execution_id=exec_id,
        output_result="Financial summary successfully generated.",
        tokens_used=1540,
        latency_ms=320,
    )
    assert completed_exec.status == "completed"
    assert completed_exec.output_result == "Financial summary successfully generated."
    assert completed_exec.tokens_used == 1540
    assert completed_exec.latency_ms == 320
    assert completed_exec.completed_at is not None


@pytest.mark.anyio
async def test_service_fail_execution(client: TestClient, setup_data, db_session: AsyncSession):
    agent_id = setup_data["agent1_id"]
    org_id = setup_data["org1_id"]

    create_res = client.post(
        f"/api/v1/agents/{agent_id}/executions",
        json={"organization_id": org_id, "input_prompt": "Fetch external report."},
    )
    exec_id = uuid.UUID(create_res.json()["id"])

    # Simulate runtime failure
    failed_exec = await agent_execution_service.fail_execution(
        db=db_session,
        execution_id=exec_id,
        error_message="Upstream service timeout",
        tokens_used=50,
        latency_ms=1000,
    )
    assert failed_exec.status == "failed"
    assert failed_exec.error_message == "Upstream service timeout"
    assert failed_exec.tokens_used == 50
    assert failed_exec.latency_ms == 1000
    assert failed_exec.completed_at is not None


# ==========================================
# 7. Audit Logging & Security Tests
# ==========================================

@pytest.mark.anyio
async def test_audit_logs_emitted_during_lifecycle(client: TestClient, setup_data, db_session: AsyncSession):
    agent_id = setup_data["agent2_id"]
    org_id = setup_data["org1_id"]
    admin_id = setup_data["user1_id"]

    # 1. Trigger -> emits agent.execution.approval_requested
    create_res = client.post(
        f"/api/v1/agents/{agent_id}/executions",
        json={"organization_id": org_id, "input_prompt": "Confidential prompt with secret key sk-12345"},
    )
    exec_id = uuid.UUID(create_res.json()["id"])

    # 2. Approve -> emits agent.execution.approved & agent.execution.started
    client.post(
        f"/api/v1/executions/{exec_id}/approve?organization_id={org_id}",
        json={"user_id": admin_id},
    )

    # 3. Complete -> emits agent.execution.completed
    await agent_execution_service.complete_execution(
        db=db_session,
        execution_id=exec_id,
        output_result="Output data",
        tokens_used=100,
        latency_ms=250,
    )

    # Query audit logs for this execution
    result = await db_session.execute(
        select(AuditLog).where(AuditLog.resource_id == exec_id).order_by(AuditLog.created_at.asc())
    )
    logs = list(result.scalars().all())
    actions = [log.action for log in logs]

    assert "agent.execution.approval_requested" in actions
    assert "agent.execution.approved" in actions
    assert "agent.execution.started" in actions
    assert "agent.execution.completed" in actions

    # Verify audit details DO NOT contain raw input prompt or raw output
    for log in logs:
        assert "sk-12345" not in str(log.details)
        assert "Confidential prompt" not in str(log.details)


# ==========================================
# 8. Cascade Deletion Tests
# ==========================================

@pytest.mark.anyio
async def test_agent_deletion_cascades_to_executions(client: TestClient, setup_data, db_session: AsyncSession):
    agent_id = setup_data["agent1_id"]
    org_id = setup_data["org1_id"]

    # Create 2 executions
    res1 = client.post(f"/api/v1/agents/{agent_id}/executions", json={"organization_id": org_id, "input_prompt": "Run A"})
    res2 = client.post(f"/api/v1/agents/{agent_id}/executions", json={"organization_id": org_id, "input_prompt": "Run B"})
    exec1_id = uuid.UUID(res1.json()["id"])
    exec2_id = uuid.UUID(res2.json()["id"])

    # Delete the agent
    del_res = client.delete(f"/api/v1/agents/{agent_id}?organization_id={org_id}")
    assert del_res.status_code == 204

    # Verify both executions were cascade-deleted
    exec1 = await db_session.get(AgentExecution, exec1_id)
    exec2 = await db_session.get(AgentExecution, exec2_id)
    assert exec1 is None
    assert exec2 is None
