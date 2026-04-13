"""
Report Generation Schemas — R-01

Request/response models for report templates, job submission, and PDF export.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.models.report import ReportOrientation, ReportStatus, ReportType

# ── Shared filter schema ───────────────────────────────────────────────────────


class ReportFilters(BaseModel):
    """Flexible filter set applied when generating a report."""

    date_from: date | None = None
    date_to: date | None = None
    # Predefined range shortcut — overrides date_from/date_to when set
    date_preset: str | None = Field(
        default=None,
        description="Predefined range: today | last_7_days | last_30_days | last_90_days",
    )
    # For moderation/violation reports
    statuses: list[str] | None = None
    severity_levels: list[str] | None = None
    violation_categories: list[str] | None = None
    # For video/user reports
    video_sources: list[str] | None = None
    user_roles: list[str] | None = None
    # Generic text search applied against relevant name/title fields
    search: str | None = None

    @model_validator(mode="after")
    def resolve_preset(self) -> ReportFilters:
        """Expand a date_preset into concrete date_from/date_to values."""
        from datetime import timedelta

        today = date.today()
        preset_map = {
            "today": (today, today),
            "last_7_days": (today - timedelta(days=7), today),
            "last_30_days": (today - timedelta(days=30), today),
            "last_90_days": (today - timedelta(days=90), today),
        }
        if self.date_preset and self.date_preset in preset_map:
            self.date_from, self.date_to = preset_map[self.date_preset]
        return self


# ── Template schemas ───────────────────────────────────────────────────────────


class ReportTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    report_type: ReportType
    filters: ReportFilters | None = None
    columns: list[str] | None = None
    orientation: ReportOrientation = ReportOrientation.PORTRAIT
    is_shared: bool = False


class ReportTemplateResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    report_type: ReportType
    filters: dict[str, Any] | None
    columns: list[str] | None
    orientation: ReportOrientation
    is_shared: bool
    owner_id: uuid.UUID
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


# ── Job request/response schemas ───────────────────────────────────────────────


class ReportGenerateRequest(BaseModel):
    """Submitted by admin to queue a report generation job."""

    title: str = Field(..., min_length=1, max_length=500)
    report_type: ReportType
    filters: ReportFilters = Field(default_factory=ReportFilters)
    columns: list[str] | None = None
    orientation: ReportOrientation = ReportOrientation.PORTRAIT
    # Optionally attach this job to an existing template
    template_id: uuid.UUID | None = None


class ReportJobResponse(BaseModel):
    id: uuid.UUID
    title: str
    report_type: ReportType
    status: ReportStatus
    filters: dict[str, Any] | None
    columns: list[str] | None
    orientation: ReportOrientation
    s3_key: str | None
    file_size_bytes: int | None
    row_count: int | None
    error_message: str | None
    celery_task_id: str | None
    template_id: uuid.UUID | None
    generated_by: uuid.UUID
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class ReportJobListResponse(BaseModel):
    items: list[ReportJobResponse]
    total: int
    page: int
    page_size: int


# ── Preview schema ─────────────────────────────────────────────────────────────


class ReportPreviewRequest(BaseModel):
    report_type: ReportType
    filters: ReportFilters = Field(default_factory=ReportFilters)
    columns: list[str] | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)


class ReportPreviewResponse(BaseModel):
    columns: list[str]
    rows: list[dict[str, Any]]
    total: int
    page: int
    page_size: int
    summary: dict[str, Any]


# ── Download URL response ──────────────────────────────────────────────────────


class ReportDownloadUrlResponse(BaseModel):
    download_url: str
    expires_in_seconds: int = 3600
    filename: str
