"""
T-01 Frame Extractor Tool

Samples frames from a video file (local path or s3:// URL) at a configurable
interval using OpenCV.  Returns base64-encoded JPEG frames and their timestamps.

Public API:
    result = extract_frames(
        video_path="s3://my-bucket/videos/v1.mp4",
        interval_seconds=2.0,
        max_frames=30,
    )
    result.frames        # list[str]  base64-encoded JPEGs
    result.timestamps    # list[float] seconds from start
    result.fps           # float
    result.duration      # float  total video duration in seconds
"""

from __future__ import annotations

import base64
import os
import tempfile

import cv2
import structlog
from pydantic import BaseModel, Field

from app.config import settings

logger = structlog.get_logger(__name__)

_INTERVAL_DEFAULT: float = 2.0
_MAX_FRAMES_DEFAULT: int = 30


# ── Output schema ─────────────────────────────────────────────────────────────


class FrameExtractionResult(BaseModel):
    frames: list[str] = Field(
        default_factory=list,
        description="Base64-encoded JPEG frames",
    )
    timestamps: list[float] = Field(
        default_factory=list,
        description="Seconds from start for each frame",
    )
    fps: float = 0.0
    duration: float = 0.0
    frame_count_extracted: int = 0
    error: str | None = None


# ── Errors ────────────────────────────────────────────────────────────────────


class FrameExtractionError(RuntimeError):
    pass


# ── S3 download helper ────────────────────────────────────────────────────────


def _download_from_s3(s3_url: str) -> str:
    """Download an S3 object to a temp file and return the local path."""
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError

    if not s3_url.startswith("s3://"):
        raise FrameExtractionError(f"Unsupported URL scheme for S3 download: {s3_url}")

    without_prefix = s3_url[5:]
    bucket, _, key = without_prefix.partition("/")
    if not key:
        raise FrameExtractionError(f"Invalid S3 URL (missing key): {s3_url}")

    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
        region_name=settings.AWS_REGION,
    )

    suffix = os.path.splitext(key)[-1] or ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        try:
            s3.download_fileobj(bucket, key, tmp)
            tmp.flush()
            return tmp.name
        except (BotoCoreError, ClientError) as exc:
            os.unlink(tmp.name)
            raise FrameExtractionError(f"S3 download failed for {s3_url}: {exc}") from exc


# ── Core extraction ───────────────────────────────────────────────────────────


def _extract_local(
    path: str,
    *,
    interval_seconds: float,
    max_frames: int,
) -> FrameExtractionResult:
    """Extract frames from a local video file using OpenCV."""
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise FrameExtractionError(f"Cannot open video: {path}")

    fps: float = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames: int = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration: float = total_frames / fps if fps > 0 else 0.0
    frame_interval: int = max(1, int(fps * interval_seconds))

    frames: list[str] = []
    timestamps: list[float] = []
    frame_idx = 0

    logger.info(
        "frame_extractor_start",
        path=path,
        fps=fps,
        total_frames=total_frames,
        interval_seconds=interval_seconds,
        max_frames=max_frames,
    )

    try:
        while len(frames) < max_frames and frame_idx < total_frames:
            cap.set(cv2.CAP_PROP_POS_FRAMES, float(frame_idx))
            ret, frame = cap.read()
            if not ret:
                break

            ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if not ok:
                logger.warning("frame_extractor_encode_failed", frame_idx=frame_idx)
                frame_idx += frame_interval
                continue

            frames.append(base64.b64encode(buf.tobytes()).decode("utf-8"))
            timestamps.append(round(frame_idx / fps, 3))
            frame_idx += frame_interval
    finally:
        cap.release()

    logger.info("frame_extractor_done", extracted=len(frames))
    return FrameExtractionResult(
        frames=frames,
        timestamps=timestamps,
        fps=fps,
        duration=duration,
        frame_count_extracted=len(frames),
    )


# ── Public API ────────────────────────────────────────────────────────────────


def extract_frames(
    video_path: str,
    *,
    interval_seconds: float = _INTERVAL_DEFAULT,
    max_frames: int = _MAX_FRAMES_DEFAULT,
) -> FrameExtractionResult:
    """
    Extract frames from a video at a fixed time interval.

    Args:
        video_path:        Local file path or s3:// URL.
        interval_seconds:  Sample one frame every N seconds (default 2.0).
        max_frames:        Maximum number of frames to return (default 30).

    Returns:
        FrameExtractionResult with base64-encoded JPEG frames and timestamps.

    Raises:
        FrameExtractionError: If the video cannot be opened, is unreadable,
                              or the S3 download fails.
    """
    tmp_to_delete: str | None = None
    local_path = video_path

    if video_path.startswith("s3://"):
        logger.info("frame_extractor_s3_download", url=video_path)
        local_path = _download_from_s3(video_path)
        tmp_to_delete = local_path

    try:
        return _extract_local(
            local_path,
            interval_seconds=interval_seconds,
            max_frames=max_frames,
        )
    finally:
        if tmp_to_delete and os.path.exists(tmp_to_delete):
            os.unlink(tmp_to_delete)
