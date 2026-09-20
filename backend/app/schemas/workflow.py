import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


VALID_WORKFLOW_STATUSES = {"Active", "Draft", "Paused"}
VALID_STEP_TYPES = {
    "Trigger",
    "AI Agent",
    "Knowledge Retrieval",
    "Action",
    "Condition",
    "Human Approval",
}
VALID_EXECUTION_STATUSES = {
    "running",
    "waiting_approval",
    "completed",
    "failed",
    "cancelled",
}


STEP_TYPE_MAP = {
    "trigger": "Trigger",
    "ai agent": "AI Agent",
    "ai_agent": "AI Agent",
    "agent": "AI Agent",
    "knowledge retrieval": "Knowledge Retrieval",
    "knowledge_retrieval": "Knowledge Retrieval",
    "retrieval": "Knowledge Retrieval",
    "action": "Action",
    "condition": "Condition",
    "human approval": "Human Approval",
    "human_approval": "Human Approval",
    "approval": "Human Approval",
}


# ==========================================
# Workflow Step Schemas
# ==========================================

class WorkflowStepBase(BaseModel):
    step_order: int = Field(default=1, ge=1, description="Display sequence order index")
    type: str = Field(..., description="Step type")
    title: str = Field(..., min_length=1, max_length=255, description="Display title")
    description: str | None = Field(None, description="Optional step summary")
    config: Dict[str, Any] = Field(default_factory=dict, description="Step configuration dictionary")
    next_step_ids: List[Any] = Field(default_factory=list, description="Outgoing graph edges")

    @model_validator(mode="before")
    @classmethod
    def normalize_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "title" not in data and "name" in data:
                data["title"] = data["name"]
            if "type" not in data and "step_type" in data:
                data["type"] = data["step_type"]
            if "step_order" not in data or data.get("step_order") is None:
                data["step_order"] = 1
        return data

    @field_validator("title")
    @classmethod
    def validate_title_not_blank(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Step title cannot be empty or whitespace.")
        return trimmed

    @field_validator("type")
    @classmethod
    def validate_step_type(cls, v: str) -> str:
        trimmed = v.strip().lower()
        if trimmed in STEP_TYPE_MAP:
            return STEP_TYPE_MAP[trimmed]
        matches = [t for t in VALID_STEP_TYPES if t.lower() == trimmed]
        if not matches:
            raise ValueError(
                f"Invalid step type: '{v}'. Must be one of {sorted(VALID_STEP_TYPES)}"
            )
        return matches[0]


class WorkflowStepCreate(WorkflowStepBase):
    id: Any | None = Field(
        None, description="Optional step UUID or identifier slug"
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_create_id(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "id" not in data and "step_id" in data:
                data["id"] = data["step_id"]
        return data


class WorkflowStepResponse(WorkflowStepBase):
    id: UUID
    workflow_id: UUID
    next_step_ids: List[UUID] = Field(default_factory=list, description="Outgoing graph edges")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkflowStepsSyncRequest(BaseModel):
    steps: List[WorkflowStepCreate] = Field(..., description="Full workflow steps graph")


# ==========================================
# Workflow Process Schemas
# ==========================================

class WorkflowBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Workflow name")
    description: str = Field(default="", description="Workflow description")
    status: str = Field("Draft", max_length=20, description="Status ('Active', 'Draft', 'Paused')")
    trigger_type: str = Field("Manual", min_length=1, max_length=100, description="Trigger category")

    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Workflow name cannot be empty or whitespace.")
        return trimmed

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        return v.strip() if v else ""

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        trimmed = v.strip().capitalize()
        if trimmed not in VALID_WORKFLOW_STATUSES:
            raise ValueError(
                f"Invalid workflow status: '{v}'. Must be one of {sorted(VALID_WORKFLOW_STATUSES)}"
            )
        return trimmed


class WorkflowStatusUpdate(BaseModel):
    status: str = Field(..., max_length=20, description="Status ('Active', 'Draft', 'Paused')")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        trimmed = v.strip().capitalize()
        if trimmed not in VALID_WORKFLOW_STATUSES:
            raise ValueError(
                f"Invalid workflow status: '{v}'. Must be one of {sorted(VALID_WORKFLOW_STATUSES)}"
            )
        return trimmed


class WorkflowCreate(BaseModel):
    organization_id: UUID = Field(..., description="Parent organization ID")
    created_by_user_id: UUID | None = Field(
        None, description="Creator user ID; resolved to an organization member if omitted"
    )
    name: str = Field(..., min_length=1, max_length=255, description="Workflow name")
    description: str = Field(default="", description="Workflow description")
    status: str = Field("Draft", max_length=20, description="Status ('Active', 'Draft', 'Paused')")
    trigger_type: str | None = Field(None, max_length=100, description="Trigger category")
    trigger: str | None = Field(None, max_length=100, description="Frontend alias for trigger_type")
    steps: List[WorkflowStepCreate] | None = Field(
        None, description="Initial workflow steps graph"
    )

    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Workflow name cannot be empty or whitespace.")
        return trimmed

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        return v.strip() if v else ""

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        trimmed = v.strip().capitalize()
        if trimmed not in VALID_WORKFLOW_STATUSES:
            raise ValueError(
                f"Invalid workflow status: '{v}'. Must be one of {sorted(VALID_WORKFLOW_STATUSES)}"
            )
        return trimmed


class WorkflowUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, min_length=1)
    status: str | None = Field(None, max_length=20)
    trigger_type: str | None = Field(None, max_length=100)
    trigger: str | None = Field(None, max_length=100)

    @field_validator("name")
    @classmethod
    def validate_name_optional(cls, v: str | None) -> str | None:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Workflow name cannot be empty or whitespace.")
            return trimmed
        return None

    @field_validator("description")
    @classmethod
    def validate_description_optional(cls, v: str | None) -> str | None:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Workflow description cannot be empty or whitespace.")
            return trimmed
        return None

    @field_validator("status")
    @classmethod
    def validate_status_optional(cls, v: str | None) -> str | None:
        if v is not None:
            trimmed = v.strip().capitalize()
            if trimmed not in VALID_WORKFLOW_STATUSES:
                raise ValueError(
                    f"Invalid workflow status: '{v}'. Must be one of {sorted(VALID_WORKFLOW_STATUSES)}"
                )
            return trimmed
        return None


class WorkflowResponse(BaseModel):
    id: UUID
    organization_id: UUID
    created_by_user_id: UUID
    name: str
    description: str
    status: str
    trigger: str
    trigger_type: str
    created_at: datetime
    updated_at: datetime
    steps: List[WorkflowStepResponse] = Field(default_factory=list)
    executions: int = 0
    success_rate: str = "100%"
    last_run: str = "Never"

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Workflow Execution Schemas
# ==========================================

class WorkflowExecuteRequest(BaseModel):
    organization_id: UUID | None = Field(None, description="Optional tenant organization isolation check")
    triggered_by_user_id: UUID | None = Field(
        None, description="Optional user ID initiating workflow execution"
    )
    trigger_payload: Dict[str, Any] = Field(default_factory=dict, description="Payload data passed to root Trigger step")


class WorkflowExecutionResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    triggered_by_user_id: UUID | None
    status: str
    started_at: datetime
    completed_at: datetime | None
    execution_log: List[Dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class WorkflowApprovalRequest(BaseModel):
    user_id: UUID = Field(..., description="User ID granting execution approval")


class WorkflowCancellationRequest(BaseModel):
    user_id: UUID | None = Field(None, description="User ID requesting execution cancellation")
    reason: str | None = Field(None, max_length=500, description="Optional cancellation reason")
