import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.moderation import ModerationStatus, ReviewAction, ViolationCategory


class ViolationItem(BaseModel):
    category: ViolationCategory
    confidence: float
    timestamp_seconds: float | None = None
    frame_url: str | None = None
    snippet: str | None = None
    details: dict[str, Any] | None = None


class ModerationResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    video_id: uuid.UUID
    status: ModerationStatus
    overall_confidence: float | None
    violations: list[ViolationItem] | None = None
    summary: str | None
    ai_model: str | None
    processing_time_ms: int | None
    reviewed_by: uuid.UUID | None
    review_action: ReviewAction | None
    review_notes: str | None
    reviewed_at: str | None
    override_by: uuid.UUID | None
    override_decision: str | None
    override_at: str | None
    created_at: datetime
    updated_at: datetime


class ModerationQueueItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    video_id: uuid.UUID
    moderation_result_id: uuid.UUID | None
    status: ModerationStatus
    priority: int
    assigned_to: uuid.UUID | None
    tenant_id: str | None
    created_at: datetime

    # Joined from Video
    video_title: str | None = None

    # Joined from ModerationResult — AI justification
    ai_summary: str | None = None  # content summary + reasoning + policy triggers
    overall_confidence: float | None = None
    violations: list[dict[str, Any]] = []  # each has category, severity, description, confidence
    ai_model: str | None = None


class SubmitReviewRequest(BaseModel):
    action: ReviewAction
    notes: str | None = None


class OverrideRequest(BaseModel):
    decision: str
    reason: str | None = None


class PaginatedQueue(BaseModel):
    items: list[ModerationQueueItemResponse]
    total: int
    page: int
    page_size: int


class ClearQueueResponse(BaseModel):
    removed: int
