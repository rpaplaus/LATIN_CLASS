import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Shared user properties."""

    email: EmailStr
    full_name: str | None = None
    is_active: bool = True


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: str = Field(min_length=8, description="Minimum 8 characters password")
    full_name: str | None = None


class UserUpdate(BaseModel):
    """Schema for updating user profile."""

    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8)
    full_name: str | None = None
    is_active: bool | None = None


class UserResponse(UserBase):
    """Schema for public user profile responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
