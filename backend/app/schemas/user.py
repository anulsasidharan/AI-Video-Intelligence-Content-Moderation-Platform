import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field

from app.models.user import UserRole


class UserBase(BaseModel):
    """Shared properties for User schemas."""

    email: EmailStr
    name: str | None = None
    role: UserRole = UserRole.OPERATOR
    tenant_id: str | None = None
    is_active: bool = True
    whatsapp_number: str | None = None


class UserCreate(UserBase):
    """Properties to receive via API on creation (admin-only endpoint)."""

    password: str = Field(..., min_length=8, description="User password (min 8 chars)")


class UserUpdate(BaseModel):
    """Properties to receive via API on update (admin-only endpoint)."""

    name: str | None = Field(None, min_length=2)
    email: EmailStr | None = None
    role: UserRole | None = None
    is_active: bool | None = None
    password: str | None = Field(None, min_length=8, description="New password (optional)")
    # Block controls
    is_blocked: bool | None = None
    blocked_reason: str | None = Field(None, max_length=500)


class UserProfileUpdate(BaseModel):
    """Fields a user can update on their own profile."""

    name: str | None = Field(None, min_length=2, max_length=255)
    whatsapp_number: str | None = Field(None, description="E.164 format, e.g. +919876543210")
    address_line1: str | None = Field(None, max_length=255)
    address_line2: str | None = Field(None, max_length=255)
    city: str | None = Field(None, max_length=128)
    state: str | None = Field(None, max_length=128)
    postal_code: str | None = Field(None, max_length=32)
    country: str | None = Field(None, max_length=128)


class UserResponse(UserBase):
    """Properties to return to client (excludes password_hash)."""

    id: uuid.UUID
    is_blocked: bool = False
    blocked_at: datetime | None = None
    blocked_reason: str | None = None
    # Address
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None
    created_at: datetime
    updated_at: datetime

    @computed_field  # type: ignore[misc]
    @property
    def organization_id(self) -> str | None:
        """Alias for tenant_id — matches frontend User type."""
        return self.tenant_id

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int


class ChangeOwnPasswordRequest(BaseModel):
    """Used by authenticated users to change their own password."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, description="New password (min 8 chars)")
