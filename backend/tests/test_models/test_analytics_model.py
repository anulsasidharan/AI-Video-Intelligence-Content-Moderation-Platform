"""Tests for D-05 AnalyticsEvent model."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from app.models.analytics import AnalyticsEvent, EventType
from app.models.user import User
from app.models.video import Video


def _make_user(db_session):
    u = User(email=f"u{uuid.uuid4()}@test.ai", password_hash="hash")
    db_session.add(u)
    return u


class TestAnalyticsEventModel:
    @pytest.mark.asyncio
    async def test_create_event_without_video(self, db_session):
        event = AnalyticsEvent(
            event_type=EventType.VIDEO_PROCESSED,
            event_date="2024-01-15",
        )
        db_session.add(event)
        await db_session.flush()

        result = await db_session.execute(
            select(AnalyticsEvent).where(AnalyticsEvent.event_date == "2024-01-15")
        )
        e = result.scalar_one()
        assert e.event_type == EventType.VIDEO_PROCESSED
        assert e.video_id is None

    @pytest.mark.asyncio
    async def test_create_event_with_video(self, db_session):
        owner = _make_user(db_session)
        await db_session.flush()

        video = Video(title=f"v{uuid.uuid4()}", owner_id=owner.id)
        db_session.add(video)
        await db_session.flush()

        event = AnalyticsEvent(
            event_type=EventType.VIOLATION_DETECTED,
            video_id=video.id,
            event_date="2024-01-16",
            category="violence",
            confidence=0.92,
        )
        db_session.add(event)
        await db_session.flush()

        result = await db_session.execute(
            select(AnalyticsEvent).where(AnalyticsEvent.video_id == video.id)
        )
        e = result.scalar_one()
        assert e.event_type == EventType.VIOLATION_DETECTED
        assert e.category == "violence"
        assert e.confidence == pytest.approx(0.92)

    @pytest.mark.asyncio
    async def test_event_type_enum_values(self, db_session):
        for et in EventType:
            event = AnalyticsEvent(event_type=et, event_date="2024-01-01")
            db_session.add(event)

        await db_session.flush()

        result = await db_session.execute(select(AnalyticsEvent))
        events = result.scalars().all()
        stored_types = {e.event_type for e in events}
        assert stored_types == set(EventType)

    @pytest.mark.asyncio
    async def test_event_with_tenant_and_extra(self, db_session):
        event = AnalyticsEvent(
            event_type=EventType.VIDEO_PROCESSED,
            event_date="2024-02-01",
            tenant_id="tenant-001",
            extra='{"fps": 30}',
        )
        db_session.add(event)
        await db_session.flush()

        result = await db_session.execute(
            select(AnalyticsEvent).where(AnalyticsEvent.tenant_id == "tenant-001")
        )
        e = result.scalar_one()
        assert e.extra == '{"fps": 30}'
