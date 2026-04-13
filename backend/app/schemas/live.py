import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.alert import AlertSeverity, StreamStatus


class StreamCreate(BaseModel):
    title: str


class StreamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    ingest_url: str | None
    status: StreamStatus
    owner_id: uuid.UUID
    tenant_id: str | None
    created_at: datetime
    stopped_at: str | None
    moderation_active: bool = False
    moderation_started_at: datetime | None = None
    moderation_stopped_at: datetime | None = None
    frames_processed: int = 0


class StreamListResponse(BaseModel):
    items: list[StreamResponse]
    total: int


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    stream_id: uuid.UUID
    severity: AlertSeverity
    category: str | None
    message: str
    frame_url: str | None
    confidence: float | None
    is_dismissed: bool
    created_at: datetime


class AlertListResponse(BaseModel):
    items: list[AlertResponse]
    total: int


class FrameSubmitRequest(BaseModel):
    """Payload the browser sends when submitting a batch of captured frames."""

    frames: list[str] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Base64-encoded JPEG frames (1-10)",
    )
    transcript_hint: str = Field(
        default="",
        max_length=500,
        description="Optional short speech transcript for this chunk",
    )


class MessageResponse(BaseModel):
    message: str
