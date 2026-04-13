"""Pydantic schemas for the notification system."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.notification import (
    NOTIFICATION_EVENT_TYPES,
    NotificationChannel,
    NotificationFrequency,
    NotificationPriority,
    NotificationStatus,
)

# ── Notification schemas ───────────────────────────────────────────────────────


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    channel: NotificationChannel
    event_type: str
    priority: NotificationPriority
    title: str
    message: str
    data: dict[str, Any] | None
    status: NotificationStatus
    scheduled_at: datetime | None
    sent_at: datetime | None
    read_at: datetime | None
    delivery_meta: dict[str, Any] | None
    retry_count: int
    tenant_id: str | None
    created_at: datetime
    updated_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    unread_count: int


class NotificationSendRequest(BaseModel):
    """Admin-initiated ad-hoc notification send."""

    user_id: uuid.UUID
    channel: NotificationChannel
    event_type: str
    priority: NotificationPriority = NotificationPriority.MEDIUM
    title: str
    message: str
    data: dict[str, Any] | None = None
    scheduled_at: datetime | None = None

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        if v not in NOTIFICATION_EVENT_TYPES:
            raise ValueError(f"Unknown event_type '{v}'. Supported: {NOTIFICATION_EVENT_TYPES}")
        return v


# ── Preference schemas ─────────────────────────────────────────────────────────


class NotificationPreferenceItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    channel: NotificationChannel
    event_type: str
    enabled: bool
    quiet_hours_start: int | None
    quiet_hours_end: int | None
    frequency: NotificationFrequency
    updated_at: datetime


class PreferenceUpsert(BaseModel):
    """Single preference entry for upsert."""

    channel: NotificationChannel
    event_type: str
    enabled: bool = True
    quiet_hours_start: int | None = None
    quiet_hours_end: int | None = None
    frequency: NotificationFrequency = NotificationFrequency.INSTANT

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        if v not in NOTIFICATION_EVENT_TYPES:
            raise ValueError(f"Unknown event_type '{v}'. Supported: {NOTIFICATION_EVENT_TYPES}")
        return v

    @field_validator("quiet_hours_start", "quiet_hours_end")
    @classmethod
    def validate_quiet_hour(cls, v: int | None) -> int | None:
        if v is not None and not (0 <= v <= 23):
            raise ValueError("quiet_hours must be between 0 and 23")
        return v


class NotificationPreferencesRequest(BaseModel):
    preferences: list[PreferenceUpsert]


class NotificationPreferencesResponse(BaseModel):
    items: list[NotificationPreferenceItem]
    total: int


# ── Dispatch helper schema (internal, used by Celery tasks) ──────────────────


class NotificationDispatchPayload(BaseModel):
    """Internal payload passed to notification Celery tasks."""

    user_id: str
    channel: str
    event_type: str
    priority: str = NotificationPriority.MEDIUM
    title: str
    message: str
    data: dict[str, Any] | None = None
    tenant_id: str | None = None
    notification_id: str | None = None
