"""
Video API — B-02
CRUD, upload URL generation, and status polling for videos.
"""

import json
import uuid
from contextlib import suppress
from datetime import UTC, datetime
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import delete as sql_delete
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, OperatorUser
from app.config import settings
from app.core.exceptions import ForbiddenError, NotFoundError
from app.dependencies import get_db
from app.models.moderation import ModerationQueueItem
from app.models.policy import Policy
from app.models.video import Video, VideoStatus
from app.schemas.video import (
    BulkDeleteRequest,
    BulkDeleteResponse,
    DuplicateCheckItem,
    DuplicateCheckResult,
    PaginatedVideos,
    UploadUrlRequest,
    UploadUrlResponse,
    UrlAnalysisRequest,
    VideoCreate,
    VideoResponse,
    VideoStatusResponse,
    VideoUpdate,
)
from app.services.storage_service import StorageService, get_storage_service

router = APIRouter(prefix="/videos", tags=["videos"])
logger = structlog.get_logger(__name__)


def _build_video_response(video: Video, storage: StorageService | None = None) -> VideoResponse:
    """Converts a Video ORM object to VideoResponse, injecting pre-signed URLs."""
    tags: list[str] | None = None
    if video.tags:
        try:
            tags = json.loads(video.tags)
        except (json.JSONDecodeError, TypeError):
            tags = None

    playback_url: str | None = None
    thumbnail_url: str | None = None
    if storage:
        if video.s3_key:
            with suppress(Exception):
                playback_url = storage.presigned_get_url(video.s3_key)
        if video.thumbnail_s3_key:
            with suppress(Exception):
                thumbnail_url = storage.presigned_get_url(video.thumbnail_s3_key)

    return VideoResponse(
        id=video.id,
        title=video.title,
        description=video.description,
        status=video.status,
        source=video.source,
        s3_key=video.s3_key,
        thumbnail_s3_key=video.thumbnail_s3_key,
        duration_seconds=video.duration_seconds,
        file_size_bytes=video.file_size_bytes,
        content_type=video.content_type,
        tags=tags,
        owner_id=video.owner_id,
        tenant_id=video.tenant_id,
        created_at=video.created_at,
        updated_at=video.updated_at,
        playback_url=playback_url,
        thumbnail_url=thumbnail_url,
    )


# ── GET /videos ───────────────────────────────────────────────────────────────


@router.get(
    "",
    response_model=PaginatedVideos,
    summary="List videos with pagination and filters",
)
async def list_videos(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    storage: Annotated[StorageService, Depends(get_storage_service)],
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    status_filter: VideoStatus | None = Query(None, alias="status"),  # noqa: B008
    q: str | None = Query(None, description="Search by title"),
) -> PaginatedVideos:
    base_query = select(Video).where(
        Video.deleted_at.is_(None),
        Video.owner_id == current_user.id,
    )
    if status_filter:
        base_query = base_query.where(Video.status == status_filter)
    if q:
        base_query = base_query.where(Video.title.ilike(f"%{q}%"))

    count_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total = count_result.scalar_one()

    result = await db.execute(
        base_query.order_by(Video.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    videos = result.scalars().all()

    return PaginatedVideos(
        items=[_build_video_response(v, storage) for v in videos],
        total=total,
        page=page,
        page_size=page_size,
    )


# ── POST /videos/upload-url ───────────────────────────────────────────────────


@router.post(
    "/upload-url",
    response_model=UploadUrlResponse,
    summary="Generate a pre-signed S3 PUT URL for direct video upload",
)
async def get_upload_url(
    body: UploadUrlRequest,
    current_user: CurrentUser,
    storage: Annotated[StorageService, Depends(get_storage_service)],
) -> UploadUrlResponse:
    s3_key = f"uploads/{current_user.id}/{uuid.uuid4()}/{body.filename}"
    upload_url = storage.presigned_put_url(
        s3_key=s3_key,
        content_type=body.content_type,
        expires=settings.S3_PRESIGNED_URL_EXPIRE,
    )

    logger.info("upload_url_generated", user_id=str(current_user.id), s3_key=s3_key)
    return UploadUrlResponse(
        upload_url=upload_url,
        s3_key=s3_key,
        expires_in=settings.S3_PRESIGNED_URL_EXPIRE,
    )


# ── POST /videos/analyze-url ─────────────────────────────────────────────────


@router.post(
    "/analyze-url",
    response_model=VideoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a web/YouTube URL for AI content moderation",
)
async def analyze_url_video(
    body: UrlAnalysisRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    storage: Annotated[StorageService, Depends(get_storage_service)],
) -> VideoResponse:
    from app.models.video import VideoSource

    # Derive a display title: explicit > URL hostname > raw URL snippet
    title = body.title or body.url[:120]

    video = Video(
        title=title,
        source=VideoSource.URL,
        source_url=body.url,
        owner_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )
    db.add(video)
    await db.flush()

    # Fetch active policy rules
    policy_result = await db.execute(
        select(Policy).where(
            Policy.is_active.is_(True),
            or_(Policy.is_default.is_(True), Policy.owner_id == current_user.id),
        )
    )
    active_policies = policy_result.scalars().all()
    policy_rules: list[dict] = []
    for p in active_policies:
        if p.rules:
            policy_rules.extend(p.rules)

    # Commit BEFORE enqueuing so the Celery worker can find the video row
    await db.commit()

    from app.workers.video_tasks import process_url_video_task

    process_url_video_task.delay(str(video.id), body.url, policy_rules)

    logger.info(
        "url_video_registered",
        video_id=str(video.id),
        user_id=str(current_user.id),
        url=body.url,
    )
    return _build_video_response(video, storage)


# ── POST /videos/check-duplicates ────────────────────────────────────────────


@router.post(
    "/check-duplicates",
    response_model=list[DuplicateCheckResult],
    summary="Check which filenames+sizes already exist for the current user",
)
async def check_duplicates(
    body: list[DuplicateCheckItem],
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[DuplicateCheckResult]:
    results: list[DuplicateCheckResult] = []
    for item in body:
        row = await db.execute(
            select(Video.id)
            .where(
                Video.title == item.filename,
                Video.file_size_bytes == item.file_size_bytes,
                Video.owner_id == current_user.id,
                Video.deleted_at.is_(None),
            )
            .limit(1)
        )
        results.append(
            DuplicateCheckResult(
                filename=item.filename,
                file_size_bytes=item.file_size_bytes,
                exists=row.scalar() is not None,
            )
        )
    return results


# ── POST /videos ──────────────────────────────────────────────────────────────


@router.post(
    "",
    response_model=VideoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a video after S3 upload and enqueue processing",
)
async def create_video(
    body: VideoCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    storage: Annotated[StorageService, Depends(get_storage_service)],
) -> VideoResponse:
    tags_json = json.dumps(body.tags) if body.tags else None

    video = Video(
        title=body.title,
        description=body.description,
        source=body.source,
        s3_key=body.s3_key,
        file_size_bytes=body.file_size_bytes,
        content_type=body.content_type,
        tags=tags_json,
        owner_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )
    db.add(video)
    await db.flush()

    # Fetch active policy rules for this user (defaults + their own active policies)
    policy_result = await db.execute(
        select(Policy).where(
            Policy.is_active.is_(True),
            or_(Policy.is_default.is_(True), Policy.owner_id == current_user.id),
        )
    )
    active_policies = policy_result.scalars().all()
    policy_rules: list[dict] = []
    for p in active_policies:
        if p.rules:
            policy_rules.extend(p.rules)

    # Commit BEFORE enqueuing so the Celery worker can find the video row
    # (worker uses a separate sync DB connection that can't see uncommitted data)
    await db.commit()

    # Enqueue the full processing + moderation pipeline
    from app.workers.video_tasks import process_video

    process_video.delay(str(video.id), body.s3_key, policy_rules)

    logger.info("video_registered", video_id=str(video.id), user_id=str(current_user.id))
    return _build_video_response(video, storage)


# ── GET /videos/{id} ──────────────────────────────────────────────────────────


@router.get("/{video_id}", response_model=VideoResponse, summary="Get video detail")
async def get_video(
    video_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    storage: Annotated[StorageService, Depends(get_storage_service)],
) -> VideoResponse:
    result = await db.execute(select(Video).where(Video.id == video_id, Video.deleted_at.is_(None)))
    video = result.scalar_one_or_none()
    if not video:
        raise NotFoundError("Video", str(video_id))

    if video.owner_id != current_user.id and current_user.tenant_id != video.tenant_id:
        raise ForbiddenError("You do not have access to this video.")

    return _build_video_response(video, storage)


# ── GET /videos/{id}/status ───────────────────────────────────────────────────


@router.get(
    "/{video_id}/status",
    response_model=VideoStatusResponse,
    summary="Poll video status",
)
async def get_video_status(
    video_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> VideoStatusResponse:
    result = await db.execute(select(Video).where(Video.id == video_id, Video.deleted_at.is_(None)))
    video = result.scalar_one_or_none()
    if not video:
        raise NotFoundError("Video", str(video_id))

    return VideoStatusResponse(
        id=video.id,
        status=video.status,
        error_message=video.error_message,
    )


# ── PUT /videos/{id} ──────────────────────────────────────────────────────────


@router.put("/{video_id}", response_model=VideoResponse, summary="Update video metadata")
async def update_video(
    video_id: uuid.UUID,
    body: VideoUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    storage: Annotated[StorageService, Depends(get_storage_service)],
) -> VideoResponse:
    result = await db.execute(select(Video).where(Video.id == video_id, Video.deleted_at.is_(None)))
    video = result.scalar_one_or_none()
    if not video:
        raise NotFoundError("Video", str(video_id))
    if video.owner_id != current_user.id:
        raise ForbiddenError("You do not own this video.")

    if body.title is not None:
        video.title = body.title
    if body.description is not None:
        video.description = body.description
    if body.tags is not None:
        video.tags = json.dumps(body.tags)

    logger.info("video_updated", video_id=str(video_id))
    return _build_video_response(video, storage)


# ── POST /videos/bulk-delete ──────────────────────────────────────────────────


@router.post(
    "/bulk-delete",
    response_model=BulkDeleteResponse,
    summary="Delete video files for multiple videos, preserving metadata and thumbnails",
)
async def bulk_delete_videos(
    body: BulkDeleteRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    storage: Annotated[StorageService, Depends(get_storage_service)],
) -> BulkDeleteResponse:
    deleted = 0
    skipped = 0
    now = datetime.now(UTC).isoformat()

    for video_id in body.video_ids:
        result = await db.execute(
            select(Video).where(Video.id == video_id, Video.deleted_at.is_(None))
        )
        video = result.scalar_one_or_none()

        if not video or video.owner_id != current_user.id:
            skipped += 1
            continue

        # Delete the video file from S3 — thumbnail is intentionally kept
        if video.s3_key:
            with suppress(Exception):
                storage.delete_object(video.s3_key)

        video.s3_key = None
        video.deleted_at = now
        video.status = VideoStatus.DELETED

        # Remove pending queue entries
        await db.execute(
            sql_delete(ModerationQueueItem).where(ModerationQueueItem.video_id == video_id)
        )

        deleted += 1
        logger.info("video_bulk_deleted", video_id=str(video_id), user_id=str(current_user.id))

    await db.commit()
    return BulkDeleteResponse(deleted=deleted, skipped=skipped)


# ── DELETE /videos/{id} ───────────────────────────────────────────────────────


@router.delete(
    "/{video_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Soft-delete a video",
)
async def delete_video(
    video_id: uuid.UUID,
    current_user: OperatorUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    result = await db.execute(select(Video).where(Video.id == video_id, Video.deleted_at.is_(None)))
    video = result.scalar_one_or_none()
    if not video:
        raise NotFoundError("Video", str(video_id))

    video.deleted_at = datetime.now(UTC).isoformat()
    video.status = VideoStatus.DELETED

    # Remove any pending queue entries for this video (deleted mid-process or after moderation)
    await db.execute(
        sql_delete(ModerationQueueItem).where(ModerationQueueItem.video_id == video_id)
    )

    # Stub: enqueue S3 cleanup — cleanup_tasks.delete_video_artifacts.delay(str(video_id))
    logger.info("video_soft_deleted", video_id=str(video_id))
