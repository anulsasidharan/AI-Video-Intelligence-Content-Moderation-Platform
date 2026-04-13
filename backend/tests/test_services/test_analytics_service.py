"""Tests for S-04 AnalyticsService — DB and Redis mocked."""

from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

# ── Helpers ────────────────────────────────────────────────────────────────────


def _make_db(scalar_value=0):
    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one.return_value = scalar_value
    result_mock.scalars.return_value.all.return_value = []
    result_mock.fetchall.return_value = []
    db.execute = AsyncMock(return_value=result_mock)
    db.scalar = AsyncMock(return_value=scalar_value)
    db.add = MagicMock()
    db.flush = AsyncMock()
    return db


def _make_redis(cached_value=None):
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=cached_value)
    redis.setex = AsyncMock()
    redis.delete = AsyncMock()
    return redis


# ── get_summary ────────────────────────────────────────────────────────────────


class TestGetSummary:
    @pytest.mark.asyncio
    async def test_returns_cached_summary_when_available(self):
        from app.schemas.analytics import AnalyticsSummary
        from app.services.analytics_service import AnalyticsService

        cached = AnalyticsSummary(
            total_videos_processed=10,
            total_violations_detected=3,
            violation_rate_percent=30.0,
            avg_confidence=0.0,
            videos_approved=0,
            videos_rejected=0,
            videos_escalated=0,
            top_violation_categories=[],
        ).model_dump_json()

        db = _make_db()
        redis = _make_redis(cached_value=cached)

        service = AnalyticsService(db=db, redis=redis)
        result = await service.get_summary()

        assert result.total_videos_processed == 10
        db.execute.assert_not_awaited()  # no DB query when cache hit

    @pytest.mark.asyncio
    async def test_builds_and_caches_summary_on_cache_miss(self):
        from app.services.analytics_service import AnalyticsService

        db = _make_db(scalar_value=5)
        redis = _make_redis(cached_value=None)

        service = AnalyticsService(db=db, redis=redis)
        result = await service.get_summary()

        redis.setex.assert_awaited_once()
        assert result.total_videos_processed == 5

    @pytest.mark.asyncio
    async def test_violation_rate_is_zero_when_no_videos(self):
        from app.services.analytics_service import AnalyticsService

        db = _make_db(scalar_value=0)
        redis = _make_redis(cached_value=None)

        service = AnalyticsService(db=db, redis=redis)
        result = await service.get_summary()

        assert result.violation_rate_percent == 0.0


# ── get_violations ─────────────────────────────────────────────────────────────


class TestGetViolations:
    @pytest.mark.asyncio
    async def test_returns_violations_response_with_defaults(self):
        from app.services.analytics_service import AnalyticsService

        db = _make_db()
        redis = _make_redis()

        service = AnalyticsService(db=db, redis=redis)
        result = await service.get_violations()

        assert result.time_series == []
        assert result.breakdown == []
        assert result.total == 0
        assert result.date_from is not None
        assert result.date_to is not None

    @pytest.mark.asyncio
    async def test_accepts_custom_date_range(self):
        from app.services.analytics_service import AnalyticsService

        db = _make_db()
        redis = _make_redis()

        service = AnalyticsService(db=db, redis=redis)
        result = await service.get_violations(
            date_from=date(2024, 1, 1),
            date_to=date(2024, 1, 31),
        )

        assert result.date_from == "2024-01-01"
        assert result.date_to == "2024-01-31"


# ── export_csv ─────────────────────────────────────────────────────────────────


class TestExportCsv:
    @pytest.mark.asyncio
    async def test_yields_csv_header_and_rows(self):
        from app.services.analytics_service import AnalyticsService

        event = MagicMock()
        event.id = "ev-1"
        event.event_date = "2024-01-15"
        event.category = "violence"
        event.confidence = 0.95
        event.video_id = "vid-1"
        event.tenant_id = "tenant-1"

        db = _make_db()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [event]
        db.execute = AsyncMock(return_value=result_mock)
        redis = _make_redis()

        service = AnalyticsService(db=db, redis=redis)
        rows = []
        async for row in service.export_csv():
            rows.append(row)

        assert rows[0].startswith("id,event_date,category")
        assert "violence" in rows[1]


# ── record_event ───────────────────────────────────────────────────────────────


class TestRecordEvent:
    @pytest.mark.asyncio
    async def test_inserts_event_and_invalidates_cache(self):
        from app.models.analytics import EventType
        from app.services.analytics_service import AnalyticsService

        db = _make_db()
        redis = _make_redis()

        service = AnalyticsService(db=db, redis=redis)
        await service.record_event(
            EventType.VIOLATION_DETECTED,
            tenant_id="t1",
            video_id="vid-1",
            category="nudity",
            confidence=0.88,
        )

        db.add.assert_called_once()
        db.flush.assert_awaited_once()
        assert redis.delete.await_count == 2  # tenant key + global key
