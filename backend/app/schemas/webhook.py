import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl

from app.models.webhook import SUPPORTED_EVENTS


class WebhookCreate(BaseModel):
    url: HttpUrl
    secret: str | None = None
    events: list[str]
    is_active: bool = True

    def validate_events(self) -> "WebhookCreate":
        invalid = [e for e in self.events if e not in SUPPORTED_EVENTS]
        if invalid:
            raise ValueError(f"Unsupported events: {invalid}. Supported: {SUPPORTED_EVENTS}")
        return self


class WebhookUpdate(BaseModel):
    url: HttpUrl | None = None
    secret: str | None = None
    events: list[str] | None = None
    is_active: bool | None = None


class WebhookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    url: str
    events: list[str] | None
    is_active: bool
    total_deliveries: int
    failed_deliveries: int
    last_delivery_at: str | None
    last_status_code: int | None
    owner_id: uuid.UUID
    tenant_id: str | None
    created_at: datetime
    updated_at: datetime


class WebhookListResponse(BaseModel):
    items: list[WebhookResponse]
    total: int


class MessageResponse(BaseModel):
    message: str
