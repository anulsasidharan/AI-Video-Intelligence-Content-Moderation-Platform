import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PolicyRule(BaseModel):
    category: str
    threshold: float = Field(..., ge=0.0, le=1.0)
    action: Literal["block", "flag", "allow"] = "flag"


class PolicyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    is_active: bool = True
    is_default: bool = False
    rules: list[PolicyRule] | None = None
    default_action: Literal["block", "flag", "allow"] = "allow"


class PolicyUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    is_active: bool | None = None
    is_default: bool | None = None
    rules: list[PolicyRule] | None = None
    default_action: Literal["block", "flag", "allow"] | None = None


class PolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    is_active: bool
    is_default: bool
    rules: list[PolicyRule] | None = None
    default_action: str
    owner_id: uuid.UUID
    tenant_id: str | None
    created_at: datetime
    updated_at: datetime


class PolicyListResponse(BaseModel):
    items: list[PolicyResponse]
    total: int
