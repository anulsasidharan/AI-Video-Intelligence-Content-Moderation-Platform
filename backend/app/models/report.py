"""
Report Generation Models — R-01

ReportTemplate: saved report configurations (admin-defined or user-saved)
ReportJob: per-generation record tracking status, S3 location, and audit trail
"""

import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class ReportType(str, enum.Enum):
    MODERATION_SUMMARY = "moderation_summary"
    VIDEO_ACTIVITY = "video_activity"
    USER_ACTIVITY = "user_activity"
    AGENT_PERFORMANCE = "agent_performance"
    VIOLATION_BREAKDOWN = "violation_breakdown"


class ReportStatus(str, enum.Enum):
    PENDING = "pending"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


class ReportOrientation(str, enum.Enum):
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"


class ReportTemplate(Base, UUIDMixin, TimestampMixin):
    """Saved report configuration that can be reused."""

    __tablename__ = "report_templates"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    report_type: Mapped[ReportType] = mapped_column(
        Enum(ReportType, name="report_type_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    # JSON-encoded filter config: date_range, categories, statuses, etc.
    filters: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON-encoded list of column names to include
    columns: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Page orientation for PDF output
    orientation: Mapped[ReportOrientation] = mapped_column(
        Enum(ReportOrientation, name="report_orientation_enum", native_enum=False),
        default=ReportOrientation.PORTRAIT,
        nullable=False,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Shared templates are visible to all admins in the same tenant
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tenant_id: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)


class ReportJob(Base, UUIDMixin, TimestampMixin):
    """Single report generation run — tracks async status and PDF artifact."""

    __tablename__ = "report_jobs"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    report_type: Mapped[ReportType] = mapped_column(
        Enum(ReportType, name="report_type_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus, name="report_status_enum", native_enum=False),
        default=ReportStatus.PENDING,
        nullable=False,
        index=True,
    )
    # JSON-encoded filters applied when generating
    filters: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON-encoded list of columns included in the report
    columns: Mapped[str | None] = mapped_column(Text, nullable=True)
    orientation: Mapped[ReportOrientation] = mapped_column(
        Enum(ReportOrientation, name="report_orientation_enum", native_enum=False),
        default=ReportOrientation.PORTRAIT,
        nullable=False,
    )
    # S3 key where the generated PDF is stored (populated when status=ready)
    s3_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Celery task ID for progress polling
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Optional link back to the template used
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("report_templates.id", ondelete="SET NULL"), nullable=True
    )
    generated_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tenant_id: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
