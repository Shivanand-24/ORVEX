import pytest
from sqlalchemy import CheckConstraint, UniqueConstraint
from app.db.base import Base
from app.models import (
    Organization,
    User,
    OrganizationMembership,
    KnowledgeSource,
    KnowledgeDocument,
    Conversation,
    AssistantMessage,
    Agent,
    AgentKnowledgeSource,
    AgentTool,
    AgentExecution,
    Workflow,
    WorkflowStep,
    WorkflowExecution,
    AuditLog,
)

EXPECTED_TABLES = {
    "organizations",
    "users",
    "organization_memberships",
    "knowledge_sources",
    "knowledge_documents",
    "conversations",
    "messages",
    "agents",
    "agent_knowledge_sources",
    "agent_tools",
    "agent_executions",
    "workflows",
    "workflow_steps",
    "workflow_executions",
    "audit_logs",
}


def test_all_15_tables_registered_in_metadata() -> None:
    """Verify that exactly all 15 required tables are registered in SQLAlchemy metadata."""
    registered_tables = set(Base.metadata.tables.keys())
    assert registered_tables == EXPECTED_TABLES
    assert len(registered_tables) == 15


def test_table_count() -> None:
    """Verify metadata contains exactly 15 tables."""
    assert len(Base.metadata.tables) == 15



def test_junction_tables_composite_primary_keys() -> None:
    """Verify agent_knowledge_sources and agent_tools use composite primary keys."""
    aks_table = Base.metadata.tables["agent_knowledge_sources"]
    aks_pk_cols = [c.name for c in aks_table.primary_key.columns]
    assert sorted(aks_pk_cols) == ["agent_id", "source_id"]

    agent_tools_table = Base.metadata.tables["agent_tools"]
    at_pk_cols = [c.name for c in agent_tools_table.primary_key.columns]
    assert sorted(at_pk_cols) == ["agent_id", "tool_name"]


def test_organization_memberships_constraints() -> None:
    """Verify unique and check constraints on organization_memberships."""
    table = Base.metadata.tables["organization_memberships"]
    constraint_names = [c.name for c in table.constraints]
    assert "uq_org_membership_user" in constraint_names
    assert "chk_membership_role" in constraint_names


def test_messages_role_check_constraint() -> None:
    """Verify role check constraint on messages table."""
    table = Base.metadata.tables["messages"]
    constraint_names = [c.name for c in table.constraints]
    assert "chk_message_role" in constraint_names


def test_timestamp_scoping_correctness() -> None:
    """Verify created_at/updated_at timestamp rules across all entities."""
    # Entities with both created_at AND updated_at
    dual_timestamp_tables = [
        "organizations",
        "users",
        "organization_memberships",
        "knowledge_sources",
        "knowledge_documents",
        "conversations",
        "agents",
        "agent_executions",
        "workflows",
        "workflow_steps",
    ]
    for table_name in dual_timestamp_tables:
        table = Base.metadata.tables[table_name]
        assert "created_at" in table.columns, f"{table_name} missing created_at"
        assert "updated_at" in table.columns, f"{table_name} missing updated_at"

    # Entities with created_at ONLY (NO updated_at)
    created_only_tables = ["messages", "audit_logs"]
    for table_name in created_only_tables:
        table = Base.metadata.tables[table_name]
        assert "created_at" in table.columns, f"{table_name} missing created_at"
        assert "updated_at" not in table.columns, f"{table_name} should NOT have updated_at"

    # Entities with custom timestamps (NO updated_at)
    wf_exec_table = Base.metadata.tables["workflow_executions"]
    assert "started_at" in wf_exec_table.columns
    assert "completed_at" in wf_exec_table.columns
    assert "updated_at" not in wf_exec_table.columns

    # Junction tables (NO timestamps)
    junction_tables = ["agent_knowledge_sources", "agent_tools"]
    for table_name in junction_tables:
        table = Base.metadata.tables[table_name]
        assert "created_at" not in table.columns, f"{table_name} should NOT have created_at"
        assert "updated_at" not in table.columns, f"{table_name} should NOT have updated_at"


def test_jsonb_columns() -> None:
    """Verify JSONB column presence on workflow_steps, workflow_executions, and audit_logs."""
    wf_steps = Base.metadata.tables["workflow_steps"]
    assert "config" in wf_steps.columns
    assert "next_step_ids" in wf_steps.columns

    wf_exec = Base.metadata.tables["workflow_executions"]
    assert "execution_log" in wf_exec.columns

    audit = Base.metadata.tables["audit_logs"]
    assert "details" in audit.columns


def test_agent_executions_constraints() -> None:
    """Verify check constraints and relationships on agent_executions table."""
    table = Base.metadata.tables["agent_executions"]
    constraint_names = [c.name for c in table.constraints]
    assert "chk_agent_execution_status" in constraint_names
    assert "chk_agent_execution_source" in constraint_names
    assert "started_at" in table.columns
    assert "completed_at" in table.columns
