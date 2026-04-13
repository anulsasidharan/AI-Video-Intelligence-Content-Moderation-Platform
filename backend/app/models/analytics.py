import enum
import uuid

from sqlalchemy import Enum, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class EventType(str, enum.Enum):
    VIDEO_PROCESSED = "video_processed"
    VIOLATION_DETECTED = "violation_detected"
    REVIEW_COMPLETED = "review_completed"
    STREAM_STARTED = "stream_started"
    STREAM_STOPPED = "stream_stopped"


class AnalyticsEvent(Base, UUIDMixin, TimestampMixin):
    """Time-series event for analytics aggregation."""

    __tablename__ = "analytics_events"

    event_type: Mapped[EventType] = mapped_column(
        Enum(EventType, name="event_type_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    video_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("videos.id", ondelete="SET NULL"), nullable=True, index=True
    )
    tenant_id: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    extra: Mapped[str | None] = mapped_column(String(1024), nullable=True)  # JSON
    event_date: Mapped[str] = mapped_column(String(10), nullable=False, index=True)  # YYYY-MM-DD
