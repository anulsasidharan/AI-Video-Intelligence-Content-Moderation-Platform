import enum
import uuid

from sqlalchemy import JSON, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class ModerationStatus(str, enum.Enum):
    PENDING = "pending"
    FLAGGED = "flagged"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class ViolationCategory(str, enum.Enum):
    VIOLENCE = "violence"
    NUDITY = "nudity"
    HATE_SPEECH = "hate_speech"
    DRUGS = "drugs"
    SPAM = "spam"
    MISINFORMATION = "misinformation"
    COPYRIGHT = "copyright"
    OTHER = "other"


class ReviewAction(str, enum.Enum):
    APPROVE = "approve"
    REJECT = "reject"
    ESCALATE = "escalate"


class ModerationResult(Base, UUIDMixin, TimestampMixin):
    """AI-generated moderation result for a video."""

    __tablename__ = "moderation_results"

    video_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("videos.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    status: Mapped[ModerationStatus] = mapped_column(
        Enum(ModerationStatus, name="moderation_status_enum", native_enum=False),
        default=ModerationStatus.PENDING,
        index=True,
        nullable=False,
    )
    overall_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    violations: Mapped[list | None] = mapped_column(JSON, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Human review fields
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    review_action: Mapped[ReviewAction | None] = mapped_column(
        Enum(ReviewAction, name="review_action_enum", native_enum=False), nullable=True
    )
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Admin override fields
    override_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    override_decision: Mapped[str | None] = mapped_column(String(64), nullable=True)
    override_at: Mapped[str | None] = mapped_column(String(64), nullable=True)


class ModerationQueueItem(Base, UUIDMixin, TimestampMixin):
    """Queue of videos awaiting human review."""

    __tablename__ = "moderation_queue"

    video_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    moderation_result_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("moderation_results.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[ModerationStatus] = mapped_column(
        Enum(ModerationStatus, name="queue_status_enum", native_enum=False),
        default=ModerationStatus.PENDING,
        index=True,
        nullable=False,
    )
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    tenant_id: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
