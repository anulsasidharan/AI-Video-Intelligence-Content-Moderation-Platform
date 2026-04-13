import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApiKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)

    model_config = ConfigDict(str_strip_whitespace=True)


class ApiKeyRename(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)

    model_config = ConfigDict(str_strip_whitespace=True)


class ApiKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    masked: str
    created_at: datetime
    last_used_at: datetime | None
    request_count: int
    status: str  # "active" | "revoked"

    model_config = ConfigDict(from_attributes=True)


class ApiKeyCreateResponse(BaseModel):
    """Returned once after key creation — includes the raw key which is never stored."""

    id: uuid.UUID
    name: str
    key: str
    masked: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApiKeyListResponse(BaseModel):
    items: list[ApiKeyResponse]
    total: int
