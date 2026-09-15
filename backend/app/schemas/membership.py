from datetime import datetime
from typing import Literal, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.user import UserResponse


class MembershipCreate(BaseModel):
    """Schema for adding a member to an organization."""

    user_id: UUID = Field(..., description="ID of the user being added")
    role: Literal["admin", "member", "analyst"] = Field(
        default="member", description="Role within organization ('admin', 'member', 'analyst')"
    )


class MembershipUpdate(BaseModel):
    """Schema for updating a member's role."""

    role: Literal["admin", "member", "analyst"] = Field(
        ..., description="Updated role within organization ('admin', 'member', 'analyst')"
    )


class MembershipResponse(BaseModel):
    """Schema for Organization Membership API responses."""

    id: UUID
    organization_id: UUID
    user_id: UUID
    role: str
    created_at: datetime
    updated_at: datetime
    user: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)
