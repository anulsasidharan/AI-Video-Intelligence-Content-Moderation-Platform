import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class AlertSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class StreamStatus(str, enum.Enum):
    ACTIVE = "active"
    STOPPED = "stopped"
    ERROR = "error"
    PENDING = "pending"


class LiveStream(Base, UUIDMixin, TimestampMixin):
    """Live stream entity."""

    __tablename__ = "live_streams"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    ingest_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[StreamStatus] = mapped_column(
        Enum(StreamStatus, name="stream_status_enum", native_enum=False),
        default=StreamStatus.PENDING,
        index=True,
        nullable=False,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tenant_id: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    stopped_at: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Live moderation control
    moderation_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    moderation_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    moderation_stopped_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    frames_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class Alert(Base, UUIDMixin, TimestampMixin):
    """Real-time moderation alert for a live stream."""

    __tablename__ = "alerts"

    stream_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("live_streams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    severity: Mapped[AlertSeverity] = mapped_column(
        Enum(AlertSeverity, name="alert_severity_enum", native_enum=False),
        default=AlertSeverity.MEDIUM,
        nullable=False,
    )
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    frame_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tenant_id: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
