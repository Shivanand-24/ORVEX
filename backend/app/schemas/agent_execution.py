from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


VALID_SOURCES = {"direct_api", "assistant_chat", "workflow_step"}


class AgentExecutionCreate(BaseModel):
    """Payload to trigger an Agent execution."""

    organization_id: UUID = Field(..., description="Organization ID owner")
    triggered_by_user_id: UUID | None = Field(
        None, description="User ID who initiated the execution run"
    )
    source: str = Field(
        "direct_api",
        max_length=50,
        description="Invocation source ('direct_api', 'assistant_chat', 'workflow_step')",
    )
    source_reference_id: UUID | None = Field(
        None, description="Optional generic UUID reference (conversation_id or workflow_step_id)"
    )
    input_prompt: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Task input prompt or instructions for the agent run",
    )

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str) -> str:
        normalized = v.strip().lower()
        if normalized not in VALID_SOURCES:
            raise ValueError(
                f"Invalid execution source: '{v}'. Must be one of {sorted(VALID_SOURCES)}"
            )
        return normalized

    @field_validator("input_prompt")
    @classmethod
    def validate_input_prompt_not_blank(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Input prompt cannot be empty or whitespace.")
        return trimmed


class AgentExecutionResponse(BaseModel):
    """Detailed response representation of an Agent execution record."""

    id: UUID
    organization_id: UUID
    agent_id: UUID
    triggered_by_user_id: UUID | None
    source: str
    source_reference_id: UUID | None
    input_prompt: str
    status: str
    require_approval: bool
    approved_by_user_id: UUID | None
    output_result: str | None
    error_message: str | None
    tokens_used: int
    latency_ms: int
    started_at: datetime
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApprovalRequest(BaseModel):
    """Payload to approve a paused execution."""

    user_id: UUID = Field(..., description="User ID granting execution approval")


class CancellationRequest(BaseModel):
    """Payload to cancel an execution."""

    user_id: UUID | None = Field(None, description="User ID requesting cancellation")
    reason: str | None = Field(
        None, max_length=500, description="Optional reason for execution cancellation"
    )
