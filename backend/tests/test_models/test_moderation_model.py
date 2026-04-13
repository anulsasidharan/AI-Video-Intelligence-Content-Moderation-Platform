"""Tests for D-03 ModerationResult and ModerationQueueItem models."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from app.models.moderation import (
    ModerationQueueItem,
    ModerationResult,
    ModerationStatus,
    ReviewAction,
)
from app.models.user import User
from app.models.video import Video


def _make_user(db_session):
    u = User(email=f"u{uuid.uuid4()}@test.ai", password_hash="hash")
    db_session.add(u)
    return u


def _make_video(owner_id):
    return Video(title=f"v{uuid.uuid4()}", owner_id=owner_id)


class TestModerationResultModel:
    @pytest.mark.asyncio
    async def test_create_moderation_result_with_defaults(self, db_session):
        user = _make_user(db_session)
        await db_session.flush()

        video = _make_video(user.id)
        db_session.add(video)
        await db_session.flush()

        result = ModerationResult(video_id=video.id)
        db_session.add(result)
        await db_session.flush()

        fetched = await db_session.execute(
            select(ModerationResult).where(ModerationResult.video_id == video.id)
        )
        mod = fetched.scalar_one()
        assert mod.status == ModerationStatus.PENDING
        assert mod.reviewed_by is None
        assert mod.override_by is None

    @pytest.mark.asyncio
    async def test_submit_review_fields(self, db_session):
        user = _make_user(db_session)
        reviewer = _make_user(db_session)
        await db_session.flush()

        video = _make_video(user.id)
        db_session.add(video)
        await db_session.flush()

        mod = ModerationResult(
            video_id=video.id,
            status=ModerationStatus.APPROVED,
            reviewed_by=reviewer.id,
            review_action=ReviewAction.APPROVE,
            review_notes="Looks clean.",
            reviewed_at="2024-01-01T12:00:00Z",
        )
        db_session.add(mod)
        await db_session.flush()

        fetched = await db_session.execute(
            select(ModerationResult).where(ModerationResult.video_id == video.id)
        )
        m = fetched.scalar_one()
        assert m.status == ModerationStatus.APPROVED
        assert m.review_action == ReviewAction.APPROVE
        assert m.review_notes == "Looks clean."

    @pytest.mark.asyncio
    async def test_violations_stored_as_json(self, db_session):
        user = _make_user(db_session)
        await db_session.flush()

        video = _make_video(user.id)
        db_session.add(video)
        await db_session.flush()

        violations = [{"category": "violence", "confidence": 0.95, "timestamp": 12.3}]
        mod = ModerationResult(video_id=video.id, violations=violations)
        db_session.add(mod)
        await db_session.flush()

        fetched = await db_session.execute(
            select(ModerationResult).where(ModerationResult.video_id == video.id)
        )
        m = fetched.scalar_one()
        assert isinstance(m.violations, list)
        assert m.violations[0]["category"] == "violence"


class TestModerationQueueItemModel:
    @pytest.mark.asyncio
    async def test_create_queue_item(self, db_session):
        user = _make_user(db_session)
        await db_session.flush()

        video = _make_video(user.id)
        db_session.add(video)
        await db_session.flush()

        item = ModerationQueueItem(video_id=video.id)
        db_session.add(item)
        await db_session.flush()

        fetched = await db_session.execute(
            select(ModerationQueueItem).where(ModerationQueueItem.video_id == video.id)
        )
        q = fetched.scalar_one()
        assert q.priority == 0
        assert q.assigned_to is None
        assert q.status == ModerationStatus.PENDING
