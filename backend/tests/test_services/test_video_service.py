"""Tests for S-02 VideoService — DB and storage mocked."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.video import VideoStatus

# ── Fixtures ───────────────────────────────────────────────────────────────────

_VID_ID = uuid.uuid4()
_OWNER_ID = uuid.uuid4()


def _make_video(vid_id=None, owner_id=None, deleted=False):
    v = MagicMock()
    v.id = vid_id or _VID_ID
    v.owner_id = owner_id or _OWNER_ID
    v.tenant_id = None
    v.title = "Test video"
    v.description = None
    v.status = VideoStatus.PENDING
    v.source = "upload"
    v.s3_key = "videos/test.mp4"
    v.thumbnail_s3_key = None
    v.duration_seconds = None
    v.file_size_bytes = 1024
    v.content_type = "video/mp4"
    v.tags = None
    v.deleted_at = "2024-01-01" if deleted else None
    v.error_message = None
    v.created_at = None
    v.updated_at = None
    return v


def _make_db(video=None):
    db = AsyncMock()
    scalar_mock = MagicMock()
    scalar_mock.scalar_one_or_none.return_value = video
    scalar_mock.scalar_one.return_value = 0
    scalar_mock.scalars.return_value.all.return_value = [video] if video else []
    db.execute = AsyncMock(return_value=scalar_mock)
    db.scalar = AsyncMock(return_value=0)
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.delete = AsyncMock()
    return db


def _make_storage():
    storage = MagicMock()
    storage.presigned_put_url.return_value = "https://s3.example.com/put"
    storage.presigned_get_url.return_value = "https://s3.example.com/get"
    return storage


# ── generate_upload_url ────────────────────────────────────────────────────────


class TestGenerateUploadUrl:
    def test_returns_presigned_url_response(self):
        from app.services.video_service import VideoService

        db = _make_db()
        storage = _make_storage()
        service = VideoService(db=db, storage=storage)

        result = service.generate_upload_url(_OWNER_ID, "myvideo.mp4", "video/mp4")

        storage.presigned_put_url.assert_called_once()
        assert result.upload_url == "https://s3.example.com/put"
        assert "myvideo.mp4" in result.s3_key


# ── create_video ───────────────────────────────────────────────────────────────


class TestCreateVideo:
    @pytest.mark.asyncio
    async def test_creates_video_and_enqueues_task(self):
        from app.schemas.video import VideoCreate
        from app.services.video_service import VideoService

        db = _make_db()
        storage = _make_storage()
        video = _make_video()
        db.add = MagicMock(side_effect=lambda v: None)
        db.flush = AsyncMock()

        body = MagicMock(spec=VideoCreate)
        body.title = "Test"
        body.description = None
        body.source = "upload"
        body.s3_key = "videos/test.mp4"
        body.file_size_bytes = 1024
        body.content_type = "video/mp4"
        body.tags = None

        with (
            patch("app.services.video_service.Video", return_value=video),
            patch("app.workers.video_tasks.process_video") as mock_task,
            patch(
                "app.services.video_service._build_video_response",
                return_value=MagicMock(),
            ),
        ):
            mock_task.delay = MagicMock()
            service = VideoService(db=db, storage=storage)
            await service.create_video(_OWNER_ID, None, body)

        db.add.assert_called_once()
        db.flush.assert_awaited_once()
        mock_task.delay.assert_called_once()


# ── get_video ──────────────────────────────────────────────────────────────────


class TestGetVideo:
    @pytest.mark.asyncio
    async def test_returns_video_for_owner(self):
        from app.services.video_service import VideoService

        video = _make_video()
        db = _make_db(video=video)
        storage = _make_storage()

        with patch(
            "app.services.video_service._build_video_response", return_value=MagicMock()
        ) as mock_build:
            service = VideoService(db=db, storage=storage)
            result = await service.get_video(_VID_ID, _OWNER_ID)

        assert result is not None
        mock_build.assert_called_once_with(video, storage)

    @pytest.mark.asyncio
    async def test_raises_not_found_when_missing(self):
        from app.services.video_service import VideoService

        db = _make_db(video=None)
        storage = _make_storage()

        service = VideoService(db=db, storage=storage)
        with pytest.raises(NotFoundError):
            await service.get_video(uuid.uuid4(), _OWNER_ID)

    @pytest.mark.asyncio
    async def test_raises_forbidden_for_wrong_owner(self):
        from app.services.video_service import VideoService

        video = _make_video(owner_id=uuid.uuid4())  # different owner
        db = _make_db(video=video)
        storage = _make_storage()

        with patch("app.services.video_service._build_video_response", return_value=MagicMock()):
            service = VideoService(db=db, storage=storage)
            with pytest.raises(ForbiddenError):
                await service.get_video(_VID_ID, _OWNER_ID)


# ── get_video_status ───────────────────────────────────────────────────────────


class TestGetVideoStatus:
    @pytest.mark.asyncio
    async def test_returns_status_response(self):
        from app.services.video_service import VideoService

        video = _make_video()
        db = _make_db(video=video)
        storage = _make_storage()

        service = VideoService(db=db, storage=storage)
        result = await service.get_video_status(_VID_ID)
        assert result.id == video.id
        assert result.status == VideoStatus.PENDING

    @pytest.mark.asyncio
    async def test_raises_not_found(self):
        from app.services.video_service import VideoService

        db = _make_db(video=None)
        storage = _make_storage()

        service = VideoService(db=db, storage=storage)
        with pytest.raises(NotFoundError):
            await service.get_video_status(uuid.uuid4())


# ── delete_video ───────────────────────────────────────────────────────────────


class TestDeleteVideo:
    @pytest.mark.asyncio
    async def test_soft_deletes_and_enqueues_cleanup(self):
        from app.services.video_service import VideoService

        video = _make_video()
        db = _make_db(video=video)
        storage = _make_storage()

        with patch("app.workers.cleanup_tasks.cleanup_temp_frames_task") as mock_cleanup:
            mock_cleanup.delay = MagicMock()
            service = VideoService(db=db, storage=storage)
            await service.delete_video(_VID_ID, _OWNER_ID)

        assert video.status == VideoStatus.DELETED
        assert video.deleted_at is not None
        mock_cleanup.delay.assert_called_once_with(str(_VID_ID))

    @pytest.mark.asyncio
    async def test_raises_not_found_on_missing_video(self):
        from app.services.video_service import VideoService

        db = _make_db(video=None)
        storage = _make_storage()

        service = VideoService(db=db, storage=storage)
        with pytest.raises(NotFoundError):
            await service.delete_video(uuid.uuid4(), _OWNER_ID)
