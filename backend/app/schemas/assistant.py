from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator

VALID_MESSAGE_ROLES = {"user", "assistant", "system"}


# ==========================================
# Conversation Schemas
# ==========================================

class ConversationBase(BaseModel):
    title: str = Field("New Conversation", min_length=1, max_length=255, description="Conversation title")

    @field_validator("title")
    @classmethod
    def validate_title_not_blank(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Conversation title cannot be empty or whitespace.")
        return trimmed


class ConversationCreate(ConversationBase):
    organization_id: UUID = Field(..., description="Organization ID owner")
    user_id: UUID | None = Field(None, description="User ID owner (resolves to org member if omitted)")


class ConversationUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255, description="Updated conversation title")

    @field_validator("title")
    @classmethod
    def validate_title_not_blank(cls, v: str | None) -> str | None:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Conversation title cannot be empty or whitespace.")
            return trimmed
        return None


class ConversationResponse(BaseModel):
    id: UUID
    organization_id: UUID
    user_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Message Schemas
# ==========================================

class MessageBase(BaseModel):
    role: str = Field(..., description="Message role ('user', 'assistant', 'system')")
    content: str = Field(..., min_length=1, description="Message text content")
    tokens_used: int = Field(0, ge=0, description="Tokens consumed during generation")
    latency_ms: int = Field(0, ge=0, description="Response generation latency in ms")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        normalized = v.strip().lower()
        if normalized not in VALID_MESSAGE_ROLES:
            raise ValueError(f"Invalid message role: '{v}'. Must be one of {sorted(VALID_MESSAGE_ROLES)}")
        return normalized

    @field_validator("content")
    @classmethod
    def validate_content_not_blank(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Message content cannot be empty or whitespace.")
        return trimmed


class MessageCreate(MessageBase):
    pass


class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    tokens_used: int
    latency_ms: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
