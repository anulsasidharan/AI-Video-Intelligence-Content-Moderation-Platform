"""
S-04 AnalyticsService

Aggregation, trend calculation, and CSV export for platform analytics.
All summary queries are cached in Redis for 5 minutes.

Public API:
    await service.get_summary(tenant_id)                          -> AnalyticsSummary
    await service.get_violations(tenant_id, date_from, date_to)  -> ViolationsResponse
    await service.export_csv(tenant_id, date_from, date_to)      -> Generator[str]
    await service.record_event(event_type, tenant_id, **kwargs)  -> None
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import date, timedelta

import redis.asyncio as aioredis
import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import AnalyticsEvent, EventType
from app.schemas.analytics import (
    AnalyticsSummary,
    ViolationBreakdown,
    ViolationDataPoint,
    ViolationsResponse,
)

logger = structlog.get_logger(__name__)

_SUMMARY_CACHE_TTL = 300  # 5 minutes


def _summary_cache_key(tenant_id: str | None) -> str:
    return f"analytics:summary:{tenant_id or 'global'}"


class AnalyticsService:
    """Platform analytics: aggregation, timeseries, and CSV export."""

    def __init__(self, db: AsyncSession, redis: aioredis.Redis) -> None:
        self._db = db
        self._redis = redis

    # ── Summary ────────────────────────────────────────────────────────────────

    async def get_summary(self, tenant_id: str | None = None) -> AnalyticsSummary:
        """
        Return aggregated platform statistics.  Result is cached for 5 minutes.

        Args:
            tenant_id: Scope to a single tenant; None returns global stats.

        Returns:
            AnalyticsSummary schema.
        """
        ckey = _summary_cache_key(tenant_id)
        cached = await self._redis.get(ckey)
        if cached:
            return AnalyticsSummary.model_validate_json(cached)

        base = select(AnalyticsEvent)
        if tenant_id:
            base = base.where(AnalyticsEvent.tenant_id == tenant_id)

        processed_count = (
            await self._db.scalar(
                select(func.count()).select_from(
                    base.where(AnalyticsEvent.event_type == EventType.VIDEO_PROCESSED).subquery()
                )
            )
            or 0
        )

        violations_count = (
            await self._db.scalar(
                select(func.count()).select_from(
                    base.where(AnalyticsEvent.event_type == EventType.VIOLATION_DETECTED).subquery()
                )
            )
            or 0
        )

        violation_rate = round(
            (violations_count / processed_count * 100) if processed_count else 0.0, 2
        )

        cat_result = await self._db.execute(
            select(AnalyticsEvent.category, func.count().label("cnt"))
            .where(AnalyticsEvent.event_type == EventType.VIOLATION_DETECTED)
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
            avg_confidence=0.0,
            videos_approved=0,
            videos_rejected=0,
            videos_escalated=0,
            top_violation_categories=top_categories,
        )

        await self._redis.setex(ckey, _SUMMARY_CACHE_TTL, summary.model_dump_json())
        logger.info("analytics_summary_built", tenant_id=tenant_id)
        return summary

    # ── Violations ─────────────────────────────────────────────────────────────

    async def get_violations(
        self,
        tenant_id: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> ViolationsResponse:
        """
        Return time-series and category breakdown of violations.

        Args:
            tenant_id: Tenant scope.
            date_from: Start date (inclusive). Defaults to 30 days ago.
            date_to:   End date (inclusive). Defaults to today.

        Returns:
            ViolationsResponse schema.
        """
        if date_from is None:
            date_from = date.today() - timedelta(days=30)
        if date_to is None:
            date_to = date.today()

        from_str = date_from.isoformat()
        to_str = date_to.isoformat()

        base_filter = [
            AnalyticsEvent.event_type == EventType.VIOLATION_DETECTED,
            AnalyticsEvent.event_date >= from_str,
            AnalyticsEvent.event_date <= to_str,
        ]
        if tenant_id:
            base_filter.append(AnalyticsEvent.tenant_id == tenant_id)

        ts_result = await self._db.execute(
            select(AnalyticsEvent.event_date, func.count().label("cnt"))
            .where(*base_filter)
            .group_by(AnalyticsEvent.event_date)
            .order_by(AnalyticsEvent.event_date)
        )
        time_series = [ViolationDataPoint(date=row.event_date, count=row.cnt) for row in ts_result]

        cat_result = await self._db.execute(
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

        return ViolationsResponse(
            time_series=time_series,
            breakdown=breakdown,
            total=total,
            date_from=from_str,
            date_to=to_str,
        )

    # ── CSV export ─────────────────────────────────────────────────────────────

    async def export_csv(
        self,
        tenant_id: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Yield CSV rows for violation events in the given date range.

        Yields:
            CSV header followed by one data row per event.
        """
        if date_from is None:
            date_from = date.today() - timedelta(days=30)
        if date_to is None:
            date_to = date.today()

        from_str = date_from.isoformat()
        to_str = date_to.isoformat()

        filters = [
            AnalyticsEvent.event_type == EventType.VIOLATION_DETECTED,
            AnalyticsEvent.event_date >= from_str,
            AnalyticsEvent.event_date <= to_str,
        ]
        if tenant_id:
            filters.append(AnalyticsEvent.tenant_id == tenant_id)

        result = await self._db.execute(
            select(AnalyticsEvent).where(*filters).order_by(AnalyticsEvent.event_date)
        )
        events = result.scalars().all()

        yield "id,event_date,category,confidence,video_id,tenant_id\n"
        for e in events:
            yield (
                f"{e.id},{e.event_date},{e.category or ''},"
                f"{e.confidence or ''},{e.video_id or ''},{e.tenant_id or ''}\n"
            )

    # ── Record event ───────────────────────────────────────────────────────────

    async def record_event(
        self,
        event_type: EventType,
        tenant_id: str | None = None,
        video_id: str | None = None,
        category: str | None = None,
        confidence: float | None = None,
    ) -> None:
        """
        Insert a single AnalyticsEvent row and invalidate the summary cache.

        Args:
            event_type: EventType enum value.
            tenant_id:  Tenant scope.
            video_id:   Associated video UUID string.
            category:   Violation category string (for VIOLATION_DETECTED events).
            confidence: Model confidence score.
        """
        event = AnalyticsEvent(
            event_type=event_type,
            tenant_id=tenant_id,
            video_id=video_id,
            category=category,
            confidence=confidence,
            event_date=date.today().isoformat(),
        )
        self._db.add(event)
        await self._db.flush()

        # Invalidate cached summary
        await self._redis.delete(_summary_cache_key(tenant_id))
        await self._redis.delete(_summary_cache_key(None))

        logger.info(
            "analytics_event_recorded",
            event_type=event_type.value,
            tenant_id=tenant_id,
            video_id=video_id,
        )
