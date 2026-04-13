"""
S-02 VideoService

Video lifecycle management: registration, metadata updates, soft-delete,
presigned upload/download URLs, and status polling.  Celery task dispatch
is called here so the API route stays thin.

Public API:
    await service.list_videos(owner_id, tenant_id, page, page_size, ...)  -> PaginatedVideos
    await service.generate_upload_url(owner_id, filename, content_type)   -> UploadUrlResponse
    await service.create_video(owner_id, tenant_id, body)                 -> VideoResponse
    await service.get_video(video_id, current_user)                       -> VideoResponse
    await service.get_video_status(video_id)                              -> VideoStatusResponse
    await service.update_video(video_id, owner_id, body)                  -> VideoResponse
    await service.delete_video(video_id, operator_id)                     -> None
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Any

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.video import Video, VideoStatus
from app.schemas.video import (
    PaginatedVideos,
    UploadUrlResponse,
    VideoCreate,
    VideoResponse,
    VideoStatusResponse,
    VideoUpdate,
)
from app.services.storage_service import StorageService

logger = structlog.get_logger(__name__)


def _build_video_response(video: Video, storage: StorageService | None = None) -> VideoResponse:
    """Convert a Video ORM row to VideoResponse, injecting presigned GET URL when available."""
    tags: list[str] | None = None
    if video.tags:
        try:
            tags = json.loads(video.tags)
        except (json.JSONDecodeError, TypeError):
            tags = None

    _s3_url: str | None = None
    if storage and video.s3_key:
        try:
            _s3_url = storage.presigned_get_url(video.s3_key)
        except Exception:
            _s3_url = None

    _thumbnail_url: str | None = None
    if storage and video.thumbnail_s3_key:
        try:
            _thumbnail_url = storage.presigned_get_url(video.thumbnail_s3_key)
        except Exception:
            _thumbnail_url = None

    return VideoResponse(
        id=video.id,
        title=video.title,
        description=video.description,
        status=video.status,
        source=video.source,
        s3_key=video.s3_key,
        thumbnail_s3_key=video.thumbnail_s3_key,
        thumbnail_url=_thumbnail_url,
        playback_url=_s3_url,
        duration_seconds=video.duration_seconds,
        file_size_bytes=video.file_size_bytes,
        content_type=video.content_type,
        tags=tags,
        owner_id=video.owner_id,
        tenant_id=video.tenant_id,
        created_at=video.created_at,
        updated_at=video.updated_at,
    )


class VideoService:
    """Business logic for video CRUD and processing pipeline dispatch."""

    def __init__(self, db: AsyncSession, storage: StorageService) -> None:
        self._db = db
        self._storage = storage

    # ── List ───────────────────────────────────────────────────────────────────

    async def list_videos(
        self,
        owner_id: uuid.UUID,
        tenant_id: str | None = None,
        page: int = 1,
        page_size: int = settings.DEFAULT_PAGE_SIZE,
        status_filter: VideoStatus | None = None,
        search: str | None = None,
    ) -> PaginatedVideos:
        """
        Return a paginated list of videos owned by the requesting user.

        Args:
            owner_id:      UUID of the requesting user.
            tenant_id:     Tenant scope (unused for filtering here — owner is sufficient).
            page:          1-based page number.
            page_size:     Items per page.
            status_filter: Optional VideoStatus enum filter.
            search:        Optional partial title search (case-insensitive).

        Returns:
            PaginatedVideos schema.
        """
        base_query = select(Video).where(
            Video.deleted_at.is_(None),
            Video.owner_id == owner_id,
        )
        if status_filter:
            base_query = base_query.where(Video.status == status_filter)
        if search:
            base_query = base_query.where(Video.title.ilike(f"%{search}%"))

        count_result = await self._db.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total = count_result.scalar_one()

        result = await self._db.execute(
            base_query.order_by(Video.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        videos = result.scalars().all()

        return PaginatedVideos(
            # Skip presigned URL generation in list view — callers that need
            # playback/thumbnail URLs should fetch the detail endpoint instead.
            items=[_build_video_response(v) for v in videos],
            total=total,
            page=page,
            page_size=page_size,
        )

    # ── Upload URL ─────────────────────────────────────────────────────────────

    def generate_upload_url(
        self,
        owner_id: uuid.UUID,
        filename: str,
        content_type: str = "video/mp4",
    ) -> UploadUrlResponse:
        """
        Generate a presigned PUT URL so the client can upload directly to S3.

        Args:
            owner_id:     UUID of the requesting user.
            filename:     Original filename (used to build the S3 key).
            content_type: MIME type of the video.

        Returns:
            UploadUrlResponse with the presigned URL, key, and expiry.
        """
        s3_key = f"uploads/{owner_id}/{uuid.uuid4()}/{filename}"
        upload_url = self._storage.presigned_put_url(
            s3_key,
            content_type=content_type,
            expires=settings.GCS_PRESIGNED_URL_EXPIRE,
        )
        logger.info("upload_url_generated", owner_id=str(owner_id), s3_key=s3_key)
        return UploadUrlResponse(
            upload_url=upload_url,
            s3_key=s3_key,
            expires_in=settings.GCS_PRESIGNED_URL_EXPIRE,
        )

    # ── Create ─────────────────────────────────────────────────────────────────

    async def create_video(
        self,
        owner_id: uuid.UUID,
        tenant_id: str | None,
        body: VideoCreate,
        policy_rules: list[dict[str, Any]] | None = None,
    ) -> VideoResponse:
        """
        Register a video row and enqueue the processing pipeline.

        Args:
            owner_id:     UUID of the uploading user.
            tenant_id:    Tenant scope.
            body:         VideoCreate schema with title, s3_key, etc.
            policy_rules: Optional active policy rule dicts passed to workers.

        Returns:
            VideoResponse for the newly created video.
        """
        tags_json = json.dumps(body.tags) if body.tags else None

        video = Video(
            title=body.title,
            description=body.description,
            source=body.source,
            s3_key=body.s3_key,
            file_size_bytes=body.file_size_bytes,
            content_type=body.content_type,
            tags=tags_json,
            owner_id=owner_id,
            tenant_id=tenant_id,
        )
        self._db.add(video)
        await self._db.flush()

        # Enqueue processing pipeline
        from app.workers.video_tasks import process_video

        process_video.delay(str(video.id), body.s3_key, policy_rules or [])

        logger.info("video_registered", video_id=str(video.id), owner_id=str(owner_id))
        return _build_video_response(video, self._storage)

    # ── Read ───────────────────────────────────────────────────────────────────

    async def get_video(
        self,
        video_id: uuid.UUID,
        requesting_user_id: uuid.UUID,
        requesting_tenant_id: str | None = None,
    ) -> VideoResponse:
        """
        Fetch a single video, enforcing ownership / tenant access.

        Raises:
            NotFoundError:  If the video doesn't exist or is deleted.
            ForbiddenError: If the user has no access to the video.

        Returns:
            VideoResponse.
        """
        result = await self._db.execute(
            select(Video).where(Video.id == video_id, Video.deleted_at.is_(None))
        )
        video = result.scalar_one_or_none()
        if not video:
            raise NotFoundError("Video", str(video_id))

        if video.owner_id != requesting_user_id and (
            requesting_tenant_id is None or video.tenant_id != requesting_tenant_id
        ):
            raise ForbiddenError("You do not have access to this video.")

        return _build_video_response(video, self._storage)

    async def get_video_status(self, video_id: uuid.UUID) -> VideoStatusResponse:
        """
        Return a lightweight status-only view of a video.

        Raises:
            NotFoundError: If the video doesn't exist or is deleted.
        """
        result = await self._db.execute(
            select(Video).where(Video.id == video_id, Video.deleted_at.is_(None))
        )
        video = result.scalar_one_or_none()
        if not video:
            raise NotFoundError("Video", str(video_id))

        return VideoStatusResponse(
            id=video.id,
            status=video.status,
            error_message=video.error_message,
        )

    # ── Update ─────────────────────────────────────────────────────────────────

    async def update_video(
        self,
        video_id: uuid.UUID,
        owner_id: uuid.UUID,
        body: VideoUpdate,
    ) -> VideoResponse:
        """
        Patch video metadata fields. Only the owner may update.

        Raises:
            NotFoundError:  If the video doesn't exist.
            ForbiddenError: If the caller doesn't own the video.
        """
        result = await self._db.execute(
            select(Video).where(Video.id == video_id, Video.deleted_at.is_(None))
        )
        video = result.scalar_one_or_none()
        if not video:
            raise NotFoundError("Video", str(video_id))
        if video.owner_id != owner_id:
            raise ForbiddenError("You do not own this video.")

        if body.title is not None:
            video.title = body.title
        if body.description is not None:
            video.description = body.description
        if body.tags is not None:
            video.tags = json.dumps(body.tags)

        logger.info("video_updated", video_id=str(video_id))
        return _build_video_response(video, self._storage)

    # ── Delete ─────────────────────────────────────────────────────────────────

    async def delete_video(
        self,
        video_id: uuid.UUID,
        operator_id: uuid.UUID,
    ) -> None:
        """
        Soft-delete a video and enqueue artifact cleanup.

        Raises:
            NotFoundError: If the video doesn't exist or is already deleted.
        """
        result = await self._db.execute(
            select(Video).where(Video.id == video_id, Video.deleted_at.is_(None))
        )
        video = result.scalar_one_or_none()
        if not video:
            raise NotFoundError("Video", str(video_id))

        video.deleted_at = datetime.now(UTC).isoformat()
        video.status = VideoStatus.DELETED

        from app.workers.cleanup_tasks import cleanup_temp_frames_task

        cleanup_temp_frames_task.delay(str(video_id))

        logger.info("video_soft_deleted", video_id=str(video_id), operator_id=str(operator_id))
