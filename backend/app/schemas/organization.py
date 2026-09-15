from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


class OrganizationCreate(BaseModel):
    """Schema for creating a new Organization."""

    name: str = Field(..., min_length=1, max_length=255, description="Organization display name")
    slug: Optional[str] = Field(None, min_length=1, max_length=255, description="URL-friendly identifier")

    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Organization name cannot be blank")
        return stripped


class OrganizationUpdate(BaseModel):
    """Schema for updating an existing Organization."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Organization display name")
    slug: Optional[str] = Field(None, min_length=1, max_length=255, description="URL-friendly identifier")

    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("Organization name cannot be blank")
            return stripped
        return v


class OrganizationResponse(BaseModel):
    """Schema for Organization API responses."""

    id: UUID
    name: str
    slug: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
