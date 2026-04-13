import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AlertResponse(BaseModel):
    id: uuid.UUID
    stream_id: uuid.UUID
    severity: str
    category: str | None
    message: str
    frame_url: str | None
    is_dismissed: bool
    tenant_id: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertListResponse(BaseModel):
    items: list[AlertResponse]
    total: int
