"""
Analytics API — B-04
Summary metrics, violation time-series, and CSV export.
"""

import uuid
from datetime import date, timedelta
from typing import Annotated

import redis.asyncio as aioredis
import structlog
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.dependencies import get_db, get_redis
from app.models.analytics import AnalyticsEvent, EventType
from app.models.user import UserRole
from app.models.video import Video
from app.schemas.analytics import (
    AnalyticsSummary,
    ViolationBreakdown,
    ViolationDataPoint,
    ViolationsResponse,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])
logger = structlog.get_logger(__name__)

_SUMMARY_CACHE_TTL = 300  # 5 minutes
_USER_MAX_DAYS = 90  # non-admin users capped to 90 days of history


def _cache_key(user_id: str, is_admin: bool, filter_user_id: str | None = None) -> str:
    if is_admin:
        return f"analytics:summary:admin:{filter_user_id or 'all'}"
    return f"analytics:summary:user:{user_id}"


def _ownership_filters(current_user, filter_user_id: uuid.UUID | None = None) -> list:
    """Return additional WHERE clauses to scope events by video ownership."""
    if current_user.role != UserRole.ADMIN:
        return [
            AnalyticsEvent.video_id.in_(select(Video.id).where(Video.owner_id == current_user.id))
        ]
    if filter_user_id:
        return [
            AnalyticsEvent.video_id.in_(select(Video.id).where(Video.owner_id == filter_user_id))
        ]
    return []


# ── GET /analytics/summary ────────────────────────────────────────────────────


@router.get(
    "/summary",
    response_model=AnalyticsSummary,
    summary="Aggregate platform statistics (cached 5 min)",
)
async def get_summary(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
    user_id: uuid.UUID | None = Query(  # noqa: B008
        default=None, description="Admin only: filter by user"
    ),
) -> AnalyticsSummary:
    is_admin = current_user.role == UserRole.ADMIN
    filter_user_id = user_id if is_admin else None
    ckey = _cache_key(
        str(current_user.id), is_admin, str(filter_user_id) if filter_user_id else None
    )

    cached = await redis.get(ckey)
    if cached:
        return AnalyticsSummary.model_validate_json(cached)

    # Build base filters: tenant + ownership
    base_filters: list = []
    if current_user.tenant_id:
        base_filters.append(AnalyticsEvent.tenant_id == current_user.tenant_id)
    base_filters.extend(_ownership_filters(current_user, filter_user_id))

    processed_count = (
        await db.scalar(
            select(func.count(AnalyticsEvent.id)).where(
                AnalyticsEvent.event_type == EventType.VIDEO_PROCESSED,
                *base_filters,
            )
        )
        or 0
    )

    violations_count = (
        await db.scalar(
            select(func.count(AnalyticsEvent.id)).where(
                AnalyticsEvent.event_type == EventType.VIOLATION_DETECTED,
                *base_filters,
            )
        )
        or 0
    )

    violation_rate = round(
        (violations_count / processed_count * 100) if processed_count else 0.0, 2
    )

    # Category breakdown (top 5)
    cat_result = await db.execute(
        select(AnalyticsEvent.category, func.count().label("cnt"))
        .where(AnalyticsEvent.event_type == EventType.VIOLATION_DETECTED, *base_filters)
        .group_by(AnalyticsEvent.category)
        .order_by(func.count().desc())
        .limit(5)
    )
    top_categories = [
        {"category": row.category or "unknown", "count": row.cnt} for row in cat_result
    ]

    summary = AnalyticsSummary(
        total_videos_processed=processed_count,
        total_violations_detected=violations_count,
        violation_rate_percent=violation_rate,
        avg_confidence=0.0,  # populated by analytics_service aggregation task
        videos_approved=0,
        videos_rejected=0,
        videos_escalated=0,
        top_violation_categories=top_categories,
    )

    await redis.setex(ckey, _SUMMARY_CACHE_TTL, summary.model_dump_json())
    return summary


# ── GET /analytics/violations ─────────────────────────────────────────────────


@router.get(
    "/violations",
    response_model=ViolationsResponse,
    summary="Time-series and category breakdown of violations",
)
async def get_violations(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    date_from: date | None = Query(default=None),  # noqa: B008
    date_to: date | None = Query(default=None),  # noqa: B008
    user_id: uuid.UUID | None = Query(  # noqa: B008
        default=None, description="Admin only: filter by user"
    ),
) -> ViolationsResponse:
    is_admin = current_user.role == UserRole.ADMIN
    today = date.today()

    # Resolve effective date range
    if is_admin:
        # Admin: defaults to all-time if not provided
        actual_to = date_to or today
        actual_from = date_from  # None = no lower bound
    else:
        # Non-admin: capped at _USER_MAX_DAYS days
        max_from = today - timedelta(days=_USER_MAX_DAYS)
        actual_to = date_to or today
        actual_from = max(date_from, max_from) if date_from else max_from

    filter_user_id = user_id if is_admin else None

    # Build filters
    base_filter: list = [AnalyticsEvent.event_type == EventType.VIOLATION_DETECTED]
    if actual_from:
        base_filter.append(AnalyticsEvent.event_date >= actual_from.isoformat())
    base_filter.append(AnalyticsEvent.event_date <= actual_to.isoformat())
    if current_user.tenant_id:
        base_filter.append(AnalyticsEvent.tenant_id == current_user.tenant_id)
    base_filter.extend(_ownership_filters(current_user, filter_user_id))

    # Time-series: group by date
    ts_result = await db.execute(
        select(AnalyticsEvent.event_date, func.count().label("cnt"))
        .where(*base_filter)
        .group_by(AnalyticsEvent.event_date)
        .order_by(AnalyticsEvent.event_date)
    )
    time_series = [ViolationDataPoint(date=row.event_date, count=row.cnt) for row in ts_result]

    # Category breakdown
    cat_result = await db.execute(
        select(AnalyticsEvent.category, func.count().label("cnt"))
        .where(*base_filter)
        .group_by(AnalyticsEvent.category)
        .order_by(func.count().desc())
    )
    cat_rows = cat_result.fetchall()
    total = sum(r.cnt for r in cat_rows)

    breakdown = [
        ViolationBreakdown(
            category=row.category or "unknown",
            count=row.cnt,
            percentage=round(row.cnt / total * 100, 2) if total else 0.0,
        )
        for row in cat_rows
    ]

    from_str = actual_from.isoformat() if actual_from else ""
    to_str = actual_to.isoformat()

    return ViolationsResponse(
        time_series=time_series,
        breakdown=breakdown,
        total=total,
        date_from=from_str,
        date_to=to_str,
    )


# ── GET /analytics/export ─────────────────────────────────────────────────────


@router.get(
    "/export",
    summary="Export violation analytics as CSV",
    response_class=StreamingResponse,
)
async def export_analytics(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    date_from: date | None = Query(default=None),  # noqa: B008
    date_to: date | None = Query(default=None),  # noqa: B008
) -> StreamingResponse:
    is_admin = current_user.role == UserRole.ADMIN
    today = date.today()

    if is_admin:
        actual_to = date_to or today
        actual_from = date_from
    else:
        max_from = today - timedelta(days=_USER_MAX_DAYS)
        actual_to = date_to or today
        actual_from = max(date_from, max_from) if date_from else max_from

    filters: list = [AnalyticsEvent.event_type == EventType.VIOLATION_DETECTED]
    if actual_from:
        filters.append(AnalyticsEvent.event_date >= actual_from.isoformat())
    filters.append(AnalyticsEvent.event_date <= actual_to.isoformat())
    if current_user.tenant_id:
        filters.append(AnalyticsEvent.tenant_id == current_user.tenant_id)
    filters.extend(_ownership_filters(current_user))

    result = await db.execute(
        select(AnalyticsEvent).where(*filters).order_by(AnalyticsEvent.event_date)
    )
    events = result.scalars().all()

    from_str = actual_from.isoformat() if actual_from else "all"
    to_str = actual_to.isoformat()

    def _generate():
        yield "id,event_date,category,confidence,video_id,tenant_id\n"
        for e in events:
            yield f"{e.id},{e.event_date},{e.category or ''},{e.confidence or ''},{e.video_id or ''},{e.tenant_id or ''}\n"

    return StreamingResponse(
        _generate(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="violations_{from_str}_{to_str}.csv"'
        },
    )
