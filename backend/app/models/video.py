import enum
import uuid

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class VideoStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    DELETED = "deleted"


class VideoSource(str, enum.Enum):
    UPLOAD = "upload"
    LIVE = "live"
    API = "api"
    URL = "url"


class Video(Base, UUIDMixin, TimestampMixin):
    """Uploaded / registered video entity."""

    __tablename__ = "videos"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[VideoStatus] = mapped_column(
        Enum(VideoStatus, name="video_status_enum", native_enum=False),
        default=VideoStatus.PENDING,
        index=True,
        nullable=False,
    )
    source: Mapped[VideoSource] = mapped_column(
        Enum(VideoSource, name="video_source_enum", native_enum=False),
        default=VideoSource.UPLOAD,
        nullable=False,
    )
    s3_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    thumbnail_s3_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array stored as text
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tenant_id: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)  # original web/YouTube URL
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    deleted_at: Mapped[str | None] = mapped_column(String(64), nullable=True)  # ISO timestamp
