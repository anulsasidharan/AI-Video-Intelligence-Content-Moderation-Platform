"""Tests for D-02 Video model."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from app.models.user import User
from app.models.video import Video, VideoSource, VideoStatus


def _make_user():
    return User(email=f"u{uuid.uuid4()}@vidshield.ai", password_hash="hash")


class TestVideoModel:
    @pytest.mark.asyncio
    async def test_create_video_with_defaults(self, db_session):
        owner = _make_user()
        db_session.add(owner)
        await db_session.flush()

        video = Video(title="Test Video", owner_id=owner.id)
        db_session.add(video)
        await db_session.flush()

        result = await db_session.execute(select(Video).where(Video.title == "Test Video"))
        fetched = result.scalar_one()

        assert fetched.status == VideoStatus.PENDING
        assert fetched.source == VideoSource.UPLOAD
        assert fetched.deleted_at is None
        assert fetched.id is not None

    @pytest.mark.asyncio
    async def test_video_status_transition(self, db_session):
        owner = _make_user()
        db_session.add(owner)
        await db_session.flush()

        video = Video(title="Processing Video", owner_id=owner.id, status=VideoStatus.PROCESSING)
        db_session.add(video)
        await db_session.flush()

        result = await db_session.execute(select(Video).where(Video.id == video.id))
        fetched = result.scalar_one()
        assert fetched.status == VideoStatus.PROCESSING

    @pytest.mark.asyncio
    async def test_video_soft_delete_field(self, db_session):
        owner = _make_user()
        db_session.add(owner)
        await db_session.flush()

        video = Video(title="Deleted Video", owner_id=owner.id, deleted_at="2024-01-01T00:00:00Z")
        db_session.add(video)
        await db_session.flush()

        result = await db_session.execute(select(Video).where(Video.id == video.id))
        fetched = result.scalar_one()
        assert fetched.deleted_at == "2024-01-01T00:00:00Z"

    @pytest.mark.asyncio
    async def test_video_source_enum(self, db_session):
        owner = _make_user()
        db_session.add(owner)
        await db_session.flush()

        video = Video(title="API Video", owner_id=owner.id, source=VideoSource.API)
        db_session.add(video)
        await db_session.flush()

        result = await db_session.execute(select(Video).where(Video.id == video.id))
        fetched = result.scalar_one()
        assert fetched.source == VideoSource.API

    @pytest.mark.asyncio
    async def test_video_optional_fields(self, db_session):
        owner = _make_user()
        db_session.add(owner)
        await db_session.flush()

        video = Video(
            title="Full Video",
            owner_id=owner.id,
            s3_key="videos/full.mp4",
            duration_seconds=120.5,
            file_size_bytes=1024 * 1024,
            content_type="video/mp4",
            tags="tag1,tag2",
        )
        db_session.add(video)
        await db_session.flush()

        result = await db_session.execute(select(Video).where(Video.id == video.id))
        fetched = result.scalar_one()
        assert fetched.s3_key == "videos/full.mp4"
        assert fetched.duration_seconds == 120.5
        assert fetched.tags == "tag1,tag2"
