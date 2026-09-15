from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """Schema for creating a new User."""

    email: EmailStr = Field(..., description="User's unique email address")
    full_name: str = Field(..., min_length=1, max_length=255, description="User's full name")

    @field_validator("full_name")
    @classmethod
    def validate_full_name_not_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Full name cannot be blank")
        return stripped


class UserResponse(BaseModel):
    """Schema for User API responses."""

    id: UUID
    email: str
    full_name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
