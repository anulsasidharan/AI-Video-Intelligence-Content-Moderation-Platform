import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.audit import AuditAction, AuditStatus


class AccessAuditLogResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None
    email: str
    username: str | None
    action: AuditAction
    status: AuditStatus
    failure_reason: str | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AccessAuditListResponse(BaseModel):
    items: list[AccessAuditLogResponse]
    total: int


class ViolationDetail(BaseModel):
    category: str | None = None
    confidence: float | None = None
    frame_ids: list[int] | None = None
    timestamp_ms: int | None = None
    timestamps: list[float] | None = None
    rule: str | None = None
    agent: str | None = None
    description: str | None = None
    severity: str | None = None


class ModerationAuditEntry(BaseModel):
    moderation_result_id: uuid.UUID
    video_id: uuid.UUID
    video_title: str | None
    status: str
    overall_confidence: float | None
    ai_model: str | None
    processing_time_ms: int | None
    violations: list[ViolationDetail]
    summary: str | None
    reviewed_by_id: uuid.UUID | None
    review_action: str | None
    review_notes: str | None
    reviewed_at: str | None
    override_decision: str | None
    override_at: str | None
    created_at: datetime


class ModerationAuditListResponse(BaseModel):
    items: list[ModerationAuditEntry]
    total: int
