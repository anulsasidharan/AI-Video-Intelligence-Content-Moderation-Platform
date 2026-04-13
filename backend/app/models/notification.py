"""
Notification Models

Two tables:
  notifications            — persisted delivery records (all channels)
  notification_preferences — per-user, per-channel, per-event-type opt-in config
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin

# ── Enumerations ───────────────────────────────────────────────────────────────


class NotificationChannel(str, enum.Enum):
    EMAIL = "email"
    IN_APP = "in_app"
    WHATSAPP = "whatsapp"


class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    READ = "read"


class NotificationPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationFrequency(str, enum.Enum):
    INSTANT = "instant"
    BATCHED = "batched"
    DAILY_DIGEST = "daily_digest"


# Canonical event type identifiers shared across channels
NOTIFICATION_EVENT_TYPES: list[str] = [
    "video.uploaded",
    "moderation.complete",
    "moderation.flagged",
    "policy.violation",
    "stream.alert",
    "batch.complete",
    "system.quota_warning",
    "system.api_error",
    "user.registered",
    "user.password_changed",
    "user.profile_updated",
]


# ── Notification ───────────────────────────────────────────────────────────────


class Notification(Base, UUIDMixin, TimestampMixin):
    """Persisted delivery record for every notification sent or queued."""

    __tablename__ = "notifications"

    # Recipient
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Classification
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel, name="notification_channel_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    priority: Mapped[NotificationPriority] = mapped_column(
        Enum(NotificationPriority, name="notification_priority_enum", native_enum=False),
        default=NotificationPriority.MEDIUM,
        nullable=False,
    )

    # Content
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Delivery lifecycle
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus, name="notification_status_enum", native_enum=False),
        default=NotificationStatus.PENDING,
        nullable=False,
        index=True,
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Delivery metadata (e.g. SendGrid message_id, Twilio SID)
    delivery_meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Retry tracking
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Multi-tenancy
    tenant_id: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)


# ── NotificationPreference ────────────────────────────────────────────────────


class NotificationPreference(Base, UUIDMixin, TimestampMixin):
    """Per-user, per-channel, per-event-type opt-in preferences."""

    __tablename__ = "notification_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel, name="notification_channel_enum", native_enum=False),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Quiet hours (0–23 inclusive); NULL means no restriction
    quiet_hours_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quiet_hours_end: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Delivery cadence
    frequency: Mapped[NotificationFrequency] = mapped_column(
        Enum(
            NotificationFrequency,
            name="notification_frequency_enum",
            native_enum=False,
        ),
        default=NotificationFrequency.INSTANT,
        nullable=False,
    )

    tenant_id: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
