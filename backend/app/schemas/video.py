import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.video import VideoSource, VideoStatus


class VideoCreate(BaseModel):
    """Payload for registering a video after S3 upload."""

    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    source: VideoSource = VideoSource.UPLOAD
    s3_key: str
    file_size_bytes: int | None = None
    content_type: str | None = None
    tags: list[str] | None = None


class VideoUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    tags: list[str] | None = None


class VideoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None
    status: VideoStatus
    source: VideoSource
    source_url: str | None = None
    s3_key: str | None
    thumbnail_s3_key: str | None
    duration_seconds: float | None
    file_size_bytes: int | None
    content_type: str | None
    tags: list[str] | None = None
    owner_id: uuid.UUID
    tenant_id: str | None
    created_at: datetime
    updated_at: datetime

    # Populated by join query — not on model directly
    playback_url: str | None = None
    thumbnail_url: str | None = None
    moderation_status: str | None = None


class VideoStatusResponse(BaseModel):
    id: uuid.UUID
    status: VideoStatus
    moderation_status: str | None = None
    error_message: str | None = None


class UploadUrlRequest(BaseModel):
    filename: str
    content_type: str = "video/mp4"
    file_size_bytes: int | None = None


class UploadUrlResponse(BaseModel):
    upload_url: str
    s3_key: str
    expires_in: int  # seconds


class PaginatedVideos(BaseModel):
    items: list[VideoResponse]
    total: int
    page: int
    page_size: int


class UrlAnalysisRequest(BaseModel):
    url: str = Field(..., min_length=10, max_length=2048)
    title: str | None = Field(None, max_length=500)


class BulkDeleteRequest(BaseModel):
    video_ids: list[uuid.UUID]


class BulkDeleteResponse(BaseModel):
    deleted: int
    skipped: int  # not owned, not found, or already deleted


class DuplicateCheckItem(BaseModel):
    filename: str
    file_size_bytes: int


class DuplicateCheckResult(BaseModel):
    filename: str
    file_size_bytes: int
    exists: bool
