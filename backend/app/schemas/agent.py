from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


VALID_AGENT_STATUSES = {"Active", "Paused"}
VALID_AGENT_DOMAINS = {
    "Security",
    "Research",
    "Data Analytics",
    "Human Resources",
    "Operations",
}


# ==========================================
# Agent Schemas
# ==========================================

class AgentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Agent display name")
    description: str = Field(..., min_length=1, description="Agent purpose and scope description")
    domain: str = Field("Research", min_length=1, max_length=100, description="Agent operational domain")
    status: str = Field("Active", max_length=20, description="Status ('Active', 'Paused')")
    system_instructions: str = Field(..., min_length=1, description="System instructions and behavior prompt")
    require_approval: bool = Field(False, description="Whether human approval is required for actions")

    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Agent name cannot be empty or whitespace.")
        return trimmed

    @field_validator("description")
    @classmethod
    def validate_description_not_blank(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Agent description cannot be empty or whitespace.")
        return trimmed

    @field_validator("domain")
    @classmethod
    def validate_domain_not_blank(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Agent domain cannot be empty or whitespace.")
        return trimmed

    @field_validator("system_instructions")
    @classmethod
    def validate_instructions_not_blank(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("System instructions cannot be empty or whitespace.")
        return trimmed

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        normalized = v.strip().capitalize()
        if normalized not in VALID_AGENT_STATUSES:
            raise ValueError(
                f"Invalid agent status: '{v}'. Must be one of {sorted(VALID_AGENT_STATUSES)}"
            )
        return normalized


class AgentCreate(AgentBase):
    organization_id: UUID = Field(..., description="Organization ID owner")
    created_by_user_id: UUID | None = Field(
        None, description="User ID creator (resolves to org member if omitted)"
    )
    tools: list[str] | None = Field(
        None, description="Initial tool identifiers to attach to the agent"
    )
    knowledge_source_ids: list[UUID] | None = Field(
        None, description="Initial knowledge source IDs to attach to the agent"
    )

    @field_validator("tools")
    @classmethod
    def validate_tools_list(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return None
        cleaned = []
        for item in v:
            t = item.strip()
            if not t:
                raise ValueError("Tool name cannot be empty or whitespace.")
            if len(t) > 100:
                raise ValueError(f"Tool name '{t}' exceeds maximum length of 100 characters.")
            cleaned.append(t)
        return cleaned


class AgentUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255, description="Updated name")
    description: str | None = Field(None, min_length=1, description="Updated description")
    domain: str | None = Field(None, min_length=1, max_length=100, description="Updated domain")
    status: str | None = Field(None, max_length=20, description="Updated status ('Active', 'Paused')")
    system_instructions: str | None = Field(
        None, min_length=1, description="Updated system instructions"
    )
    require_approval: bool | None = Field(
        None, description="Updated human approval requirement"
    )

    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, v: str | None) -> str | None:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Agent name cannot be empty or whitespace.")
            return trimmed
        return None

    @field_validator("description")
    @classmethod
    def validate_description_not_blank(cls, v: str | None) -> str | None:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Agent description cannot be empty or whitespace.")
            return trimmed
        return None

    @field_validator("domain")
    @classmethod
    def validate_domain_not_blank(cls, v: str | None) -> str | None:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Agent domain cannot be empty or whitespace.")
            return trimmed
        return None

    @field_validator("system_instructions")
    @classmethod
    def validate_instructions_not_blank(cls, v: str | None) -> str | None:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("System instructions cannot be empty or whitespace.")
            return trimmed
        return None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v is not None:
            normalized = v.strip().capitalize()
            if normalized not in VALID_AGENT_STATUSES:
                raise ValueError(
                    f"Invalid agent status: '{v}'. Must be one of {sorted(VALID_AGENT_STATUSES)}"
                )
            return normalized
        return None


class AgentResponse(BaseModel):
    id: UUID
    organization_id: UUID
    created_by_user_id: UUID
    name: str
    description: str
    domain: str
    status: str
    system_instructions: str
    require_approval: bool
    tools: list[str] = []
    knowledge_source_ids: list[UUID] = []
    owner: str | None = None
    created_at: datetime
    updated_at: datetime

    # Mock presentation metrics for seamless UI compatibility
    executions: int = 0
    success_rate: str = "100%"
    last_run: str = "Never"

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Relationship Operation Schemas
# ==========================================

class AgentToolAttach(BaseModel):
    tool_name: str = Field(..., min_length=1, max_length=100, description="Tool registry identifier")

    @field_validator("tool_name")
    @classmethod
    def validate_tool_name_not_blank(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Tool name cannot be empty or whitespace.")
        return trimmed


class AgentKnowledgeSourceAttach(BaseModel):
    source_id: UUID = Field(..., description="Knowledge source UUID to attach to the agent")
