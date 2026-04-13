"""
Report Service — R-02

Handles:
- Report template CRUD
- Report job creation and status management
- Per-report-type data aggregation queries (used for both preview and PDF generation)
- Presigned download URL generation
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Any

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_audit import AgentAuditLog, AgentAuditStatus
from app.models.analytics import AnalyticsEvent, EventType
from app.models.moderation import ModerationResult
from app.models.report import ReportJob, ReportStatus, ReportTemplate, ReportType
from app.models.user import User
from app.models.video import Video
from app.schemas.report import (
    ReportFilters,
    ReportGenerateRequest,
    ReportTemplateCreate,
)

logger = structlog.get_logger(__name__)

# ── Helpers ────────────────────────────────────────────────────────────────────

_DEFAULT_COLUMNS: dict[ReportType, list[str]] = {
    ReportType.MODERATION_SUMMARY: [
        "video_id",
        "video_title",
        "status",
        "overall_confidence",
        "violation_count",
        "ai_model",
        "processing_time_ms",
        "created_at",
    ],
    ReportType.VIDEO_ACTIVITY: [
        "video_id",
        "title",
        "status",
        "source",
        "duration_seconds",
        "file_size_bytes",
        "owner_email",
        "created_at",
    ],
    ReportType.USER_ACTIVITY: [
        "user_id",
        "email",
        "name",
        "role",
        "is_active",
        "created_at",
    ],
    ReportType.AGENT_PERFORMANCE: [
        "trace_id",
        "agent_name",
        "status",
        "duration_ms",
        "input_tokens",
        "output_tokens",
        "error_message",
        "created_at",
    ],
    ReportType.VIOLATION_BREAKDOWN: [
        "event_date",
        "category",
        "count",
        "avg_confidence",
        "video_count",
    ],
}


def _apply_date_filter(query_filters: list, model_col: Any, rf: ReportFilters) -> None:
    """Append SQLAlchemy date range clauses in-place."""
    if rf.date_from:
        query_filters.append(model_col >= rf.date_from.isoformat())
    if rf.date_to:
        query_filters.append(model_col <= rf.date_to.isoformat())


# ── Template CRUD ──────────────────────────────────────────────────────────────


async def create_template(
    db: AsyncSession,
    payload: ReportTemplateCreate,
    owner: User,
) -> ReportTemplate:
    template = ReportTemplate(
        name=payload.name,
        description=payload.description,
        report_type=payload.report_type,
        filters=payload.filters.model_dump_json() if payload.filters else None,
        columns=json.dumps(payload.columns) if payload.columns else None,
        orientation=payload.orientation,
        owner_id=owner.id,
        is_shared=payload.is_shared,
        tenant_id=owner.tenant_id,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    logger.info("report_template_created", template_id=str(template.id), name=template.name)
    return template


async def list_templates(db: AsyncSession, owner: User) -> list[ReportTemplate]:
    filters = [ReportTemplate.owner_id == owner.id]
    if owner.tenant_id:
        filters = [
            (ReportTemplate.owner_id == owner.id)
            | (ReportTemplate.is_shared & (ReportTemplate.tenant_id == owner.tenant_id))
        ]
    result = await db.execute(
        select(ReportTemplate).where(*filters).order_by(ReportTemplate.created_at.desc())
    )
    return list(result.scalars().all())


async def delete_template(db: AsyncSession, template_id: uuid.UUID, owner: User) -> bool:
    result = await db.execute(
        select(ReportTemplate).where(
            ReportTemplate.id == template_id,
            ReportTemplate.owner_id == owner.id,
        )
    )
    tmpl = result.scalar_one_or_none()
    if not tmpl:
        return False
    await db.delete(tmpl)
    await db.commit()
    return True


# ── Job management ─────────────────────────────────────────────────────────────


async def create_job(
    db: AsyncSession,
    payload: ReportGenerateRequest,
    requester: User,
) -> ReportJob:
    job = ReportJob(
        title=payload.title,
        report_type=payload.report_type,
        status=ReportStatus.PENDING,
        filters=payload.filters.model_dump_json(),
        columns=json.dumps(payload.columns) if payload.columns else None,
        orientation=payload.orientation,
        template_id=payload.template_id,
        generated_by=requester.id,
        tenant_id=requester.tenant_id,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    logger.info("report_job_created", job_id=str(job.id), type=job.report_type.value)
    return job


async def get_job(db: AsyncSession, job_id: uuid.UUID, requester: User) -> ReportJob | None:
    result = await db.execute(
        select(ReportJob).where(
            ReportJob.id == job_id,
            ReportJob.generated_by == requester.id,
        )
    )
    return result.scalar_one_or_none()


async def list_jobs(
    db: AsyncSession,
    requester: User,
    page: int = 1,
    page_size: int = 20,
    status: ReportStatus | None = None,
) -> tuple[list[ReportJob], int]:
    base = [ReportJob.generated_by == requester.id]
    if status:
        base.append(ReportJob.status == status)

    total = await db.scalar(select(func.count(ReportJob.id)).where(*base)) or 0
    result = await db.execute(
        select(ReportJob)
        .where(*base)
        .order_by(ReportJob.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(result.scalars().all()), total


async def mark_job_generating(db: AsyncSession, job_id: uuid.UUID, celery_task_id: str) -> None:
    result = await db.execute(select(ReportJob).where(ReportJob.id == job_id))
    job = result.scalar_one_or_none()
    if job:
        job.status = ReportStatus.GENERATING
        job.celery_task_id = celery_task_id
        await db.commit()


async def mark_job_ready(
    db: AsyncSession,
    job_id: uuid.UUID,
    s3_key: str,
    file_size_bytes: int,
    row_count: int,
) -> None:
    result = await db.execute(select(ReportJob).where(ReportJob.id == job_id))
    job = result.scalar_one_or_none()
    if job:
        job.status = ReportStatus.READY
        job.s3_key = s3_key
        job.file_size_bytes = file_size_bytes
        job.row_count = row_count
        await db.commit()
    logger.info("report_job_ready", job_id=str(job_id), s3_key=s3_key)


async def mark_job_failed(db: AsyncSession, job_id: uuid.UUID, error_message: str) -> None:
    result = await db.execute(select(ReportJob).where(ReportJob.id == job_id))
    job = result.scalar_one_or_none()
    if job:
        job.status = ReportStatus.FAILED
        job.error_message = error_message
        await db.commit()
    logger.error("report_job_failed", job_id=str(job_id), error=error_message)


async def delete_job(db: AsyncSession, job_id: uuid.UUID, requester: User) -> bool:
    result = await db.execute(
        select(ReportJob).where(
            ReportJob.id == job_id,
            ReportJob.generated_by == requester.id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        return False
    await db.delete(job)
    await db.commit()
    return True


# ── Data aggregation (shared by preview API and PDF worker) ────────────────────


def _parse_filters(job_or_request: ReportJob | ReportFilters) -> ReportFilters:
    """Extract a ReportFilters object from a job (stored as JSON) or return directly."""
    if isinstance(job_or_request, ReportFilters):
        return job_or_request
    raw = job_or_request.filters
    if not raw:
        return ReportFilters()
    return ReportFilters.model_validate_json(raw)


def _resolve_columns(report_type: ReportType, requested: list[str] | None) -> list[str]:
    defaults = _DEFAULT_COLUMNS.get(report_type, [])
    if not requested:
        return defaults
    # Preserve requested order; fall back to defaults for unknowns
    return [c for c in requested if c in defaults] or defaults


async def fetch_report_data(
    db: AsyncSession,
    report_type: ReportType,
    filters: ReportFilters,
    columns: list[str] | None = None,
    page: int = 1,
    page_size: int = 500,
) -> dict[str, Any]:
    """
    Fetch paginated rows and summary statistics for a given report type.
    Returns: { columns, rows, total, summary }
    """
    cols = _resolve_columns(report_type, columns)
    handler = _REPORT_HANDLERS.get(report_type)
    if handler is None:
        return {"columns": cols, "rows": [], "total": 0, "summary": {}}
    return await handler(db, filters, cols, page, page_size)


# ── Per-type handlers ──────────────────────────────────────────────────────────


async def _moderation_summary(
    db: AsyncSession, rf: ReportFilters, cols: list[str], page: int, page_size: int
) -> dict[str, Any]:
    base: list = []
    if rf.statuses:
        base.append(ModerationResult.status.in_(rf.statuses))
    if rf.date_from:
        base.append(
            ModerationResult.created_at
            >= datetime(rf.date_from.year, rf.date_from.month, rf.date_from.day, tzinfo=UTC)
        )
    if rf.date_to:
        base.append(
            ModerationResult.created_at
            <= datetime(
                rf.date_to.year,
                rf.date_to.month,
                rf.date_to.day,
                23,
                59,
                59,
                tzinfo=UTC,
            )
        )

    total = await db.scalar(select(func.count(ModerationResult.id)).where(*base)) or 0

    result = await db.execute(
        select(ModerationResult, Video.title.label("video_title"))
        .join(Video, Video.id == ModerationResult.video_id, isouter=True)
        .where(*base)
        .order_by(ModerationResult.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows_raw = result.all()

    rows = []
    for mr, video_title in rows_raw:
        violation_count = len(mr.violations) if mr.violations else 0
        row: dict[str, Any] = {
            "video_id": str(mr.video_id),
            "video_title": video_title or "—",
            "status": mr.status.value,
            "overall_confidence": round(mr.overall_confidence or 0.0, 4),
            "violation_count": violation_count,
            "ai_model": mr.ai_model or "—",
            "processing_time_ms": mr.processing_time_ms,
            "created_at": mr.created_at.isoformat() if mr.created_at else "—",
        }
        rows.append({c: row.get(c, "—") for c in cols})

    # Summary statistics
    summary_result = await db.execute(
        select(
            ModerationResult.status,
            func.count().label("cnt"),
            func.avg(ModerationResult.overall_confidence).label("avg_conf"),
        )
        .where(*base)
        .group_by(ModerationResult.status)
    )
    by_status: dict[str, int] = {}
    avg_conf = 0.0
    total_for_avg = 0
    for s_row in summary_result:
        by_status[s_row.status.value] = s_row.cnt
        if s_row.avg_conf:
            avg_conf += s_row.avg_conf * s_row.cnt
            total_for_avg += s_row.cnt

    summary = {
        "total": total,
        "by_status": by_status,
        "avg_confidence": round(avg_conf / total_for_avg, 4) if total_for_avg else 0.0,
    }
    return {"columns": cols, "rows": rows, "total": total, "summary": summary}


async def _video_activity(
    db: AsyncSession, rf: ReportFilters, cols: list[str], page: int, page_size: int
) -> dict[str, Any]:
    base: list = []
    if rf.video_sources:
        base.append(Video.source.in_(rf.video_sources))
    if rf.date_from:
        base.append(
            Video.created_at
            >= datetime(rf.date_from.year, rf.date_from.month, rf.date_from.day, tzinfo=UTC)
        )
    if rf.date_to:
        base.append(
            Video.created_at
            <= datetime(
                rf.date_to.year,
                rf.date_to.month,
                rf.date_to.day,
                23,
                59,
                59,
                tzinfo=UTC,
            )
        )
    if rf.statuses:
        base.append(Video.status.in_(rf.statuses))

    total = await db.scalar(select(func.count(Video.id)).where(*base)) or 0

    result = await db.execute(
        select(Video, User.email.label("owner_email"))
        .join(User, User.id == Video.owner_id, isouter=True)
        .where(*base)
        .order_by(Video.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    rows = []
    total_size = 0
    total_duration = 0.0
    for v, owner_email in result.all():
        total_size += v.file_size_bytes or 0
        total_duration += v.duration_seconds or 0.0
        row: dict[str, Any] = {
            "video_id": str(v.id),
            "title": v.title,
            "status": v.status.value,
            "source": v.source.value,
            "duration_seconds": v.duration_seconds,
            "file_size_bytes": v.file_size_bytes,
            "owner_email": owner_email or "—",
            "created_at": v.created_at.isoformat() if v.created_at else "—",
        }
        rows.append({c: row.get(c, "—") for c in cols})

    summary = {
        "total": total,
        "total_size_bytes": total_size,
        "total_duration_seconds": round(total_duration, 1),
        "by_status": {},
    }
    status_result = await db.execute(
        select(Video.status, func.count().label("cnt")).where(*base).group_by(Video.status)
    )
    for s_row in status_result:
        summary["by_status"][s_row.status.value] = s_row.cnt

    return {"columns": cols, "rows": rows, "total": total, "summary": summary}


async def _user_activity(
    db: AsyncSession, rf: ReportFilters, cols: list[str], page: int, page_size: int
) -> dict[str, Any]:
    base: list = []
    if rf.user_roles:
        base.append(User.role.in_(rf.user_roles))
    if rf.date_from:
        base.append(
            User.created_at
            >= datetime(rf.date_from.year, rf.date_from.month, rf.date_from.day, tzinfo=UTC)
        )
    if rf.date_to:
        base.append(
            User.created_at
            <= datetime(
                rf.date_to.year,
                rf.date_to.month,
                rf.date_to.day,
                23,
                59,
                59,
                tzinfo=UTC,
            )
        )

    total = await db.scalar(select(func.count(User.id)).where(*base)) or 0

    result = await db.execute(
        select(User)
        .where(*base)
        .order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    rows = []
    for u in result.scalars().all():
        row: dict[str, Any] = {
            "user_id": str(u.id),
            "email": u.email,
            "name": u.name or "—",
            "role": u.role.value,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else "—",
        }
        rows.append({c: row.get(c, "—") for c in cols})

    by_role: dict[str, int] = {}
    role_result = await db.execute(
        select(User.role, func.count().label("cnt")).where(*base).group_by(User.role)
    )
    for r_row in role_result:
        by_role[r_row.role.value] = r_row.cnt

    summary = {"total": total, "by_role": by_role}
    return {"columns": cols, "rows": rows, "total": total, "summary": summary}


async def _agent_performance(
    db: AsyncSession, rf: ReportFilters, cols: list[str], page: int, page_size: int
) -> dict[str, Any]:
    base: list = []
    if rf.date_from:
        base.append(
            AgentAuditLog.created_at
            >= datetime(rf.date_from.year, rf.date_from.month, rf.date_from.day, tzinfo=UTC)
        )
    if rf.date_to:
        base.append(
            AgentAuditLog.created_at
            <= datetime(
                rf.date_to.year,
                rf.date_to.month,
                rf.date_to.day,
                23,
                59,
                59,
                tzinfo=UTC,
            )
        )

    total = await db.scalar(select(func.count(AgentAuditLog.id)).where(*base)) or 0

    result = await db.execute(
        select(AgentAuditLog)
        .where(*base)
        .order_by(AgentAuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    rows = []
    for al in result.scalars().all():
        st = al.status.value if hasattr(al.status, "value") else str(al.status)
        row: dict[str, Any] = {
            # Column keys align with admin UI / PDF templates (legacy names).
            "trace_id": al.trace_id or "—",
            "agent_name": al.agent_id or "—",
            "status": st,
            "duration_ms": al.execution_time_ms,
            "input_tokens": "—",  # not stored on agent_audit_logs
            "output_tokens": "—",
            "error_message": (
                (al.output_summary or "—") if al.status == AgentAuditStatus.FAILED else "—"
            ),
            "created_at": al.created_at.isoformat() if al.created_at else "—",
        }
        rows.append({c: row.get(c, "—") for c in cols})

    summary: dict[str, Any] = {"total": total}
    return {"columns": cols, "rows": rows, "total": total, "summary": summary}


async def _violation_breakdown(
    db: AsyncSession, rf: ReportFilters, cols: list[str], page: int, page_size: int
) -> dict[str, Any]:
    base: list = [AnalyticsEvent.event_type == EventType.VIOLATION_DETECTED]
    if rf.date_from:
        base.append(AnalyticsEvent.event_date >= rf.date_from.isoformat())
    if rf.date_to:
        base.append(AnalyticsEvent.event_date <= rf.date_to.isoformat())
    if rf.violation_categories:
        base.append(AnalyticsEvent.category.in_(rf.violation_categories))

    # Group by date + category
    grouped = await db.execute(
        select(
            AnalyticsEvent.event_date,
            AnalyticsEvent.category,
            func.count().label("cnt"),
            func.avg(AnalyticsEvent.confidence).label("avg_conf"),
            func.count(AnalyticsEvent.video_id.distinct()).label("video_count"),
        )
        .where(*base)
        .group_by(AnalyticsEvent.event_date, AnalyticsEvent.category)
        .order_by(AnalyticsEvent.event_date.desc(), func.count().desc())
    )
    all_rows = grouped.all()
    total = len(all_rows)
    paged = all_rows[(page - 1) * page_size : page * page_size]

    rows = []
    for g in paged:
        row: dict[str, Any] = {
            "event_date": str(g.event_date),
            "category": g.category or "unknown",
            "count": g.cnt,
            "avg_confidence": round(g.avg_conf or 0.0, 4),
            "video_count": g.video_count,
        }
        rows.append({c: row.get(c, "—") for c in cols})

    overall_total = sum(r.cnt for r in all_rows)
    summary = {"total_violations": overall_total, "unique_date_category_pairs": total}
    return {"columns": cols, "rows": rows, "total": total, "summary": summary}


_REPORT_HANDLERS = {
    ReportType.MODERATION_SUMMARY: _moderation_summary,
    ReportType.VIDEO_ACTIVITY: _video_activity,
    ReportType.USER_ACTIVITY: _user_activity,
    ReportType.AGENT_PERFORMANCE: _agent_performance,
    ReportType.VIOLATION_BREAKDOWN: _violation_breakdown,
}
