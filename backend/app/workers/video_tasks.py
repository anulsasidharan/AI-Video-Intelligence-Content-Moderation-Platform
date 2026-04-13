"""
W-02 Video Tasks

Async video processing pipeline triggered after a video is registered.
All heavy AI work runs in the Celery worker process; the FastAPI request
path is never blocked.

Task execution order for a full pipeline run:

    process_video(video_id, s3_key)
        ├── extract_frames_task(video_id, s3_url)
        ├── transcribe_audio_task(video_id, local_path)
        ├── generate_thumbnail_task(video_id, s3_key)
        └── run_analysis_pipeline_task(video_id, s3_url, policy_rules)

Public entry point:
    process_video.delay(video_id="...", s3_key="videos/abc.mp4")
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import tempfile
import uuid
from datetime import UTC, datetime
from typing import Any

import boto3
import structlog
from celery import shared_task

from app.ai.graphs.video_analysis_graph import run_video_analysis
from app.ai.tools.audio_transcriber import transcribe_audio
from app.ai.tools.frame_extractor import FrameExtractionError, extract_frames
from app.config import settings
from app.models.analytics import AnalyticsEvent, EventType
from app.models.moderation import ModerationResult, ModerationStatus
from app.models.video import Video, VideoStatus
from app.workers.celery_app import sync_session

logger = structlog.get_logger(__name__)


# ── Helpers ────────────────────────────────────────────────────────────────────


def _s3_url(s3_key: str) -> str:
    """Build an s3:// URL from a storage key."""
    return f"s3://{settings.S3_BUCKET_NAME}/{s3_key}"


def _s3_client():
    return boto3.client(
        "s3",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
    )


def _set_video_status(video_id: str, status: VideoStatus, error: str | None = None) -> None:
    """Update the video row status in the database."""
    with sync_session() as db:
        video = db.get(Video, uuid.UUID(video_id))
        if video:
            video.status = status
            if error:
                video.error_message = error
            video.updated_at = datetime.now(UTC)


# ── W-02-A: Frame extraction ───────────────────────────────────────────────────


@shared_task(
    bind=True,
    name="app.workers.video_tasks.extract_frames_task",
    max_retries=3,
    default_retry_delay=30,
)
def extract_frames_task(
    self,
    video_id: str,
    s3_key: str,
    interval_seconds: float = 2.0,
    max_frames: int = 30,
) -> dict[str, Any]:
    """
    Extract frames from an S3-hosted video using T-01 FrameExtractor.

    Returns:
        {"frames": [...], "timestamps": [...], "fps": float, "duration": float}
    """
    logger.info("extract_frames_task_start", video_id=video_id, s3_key=s3_key)
    try:
        result = extract_frames(
            _s3_url(s3_key),
            interval_seconds=interval_seconds,
            max_frames=max_frames,
        )
        logger.info(
            "extract_frames_task_done",
            video_id=video_id,
            frame_count=result.frame_count_extracted,
        )
        return {
            "frames": result.frames,
            "timestamps": result.timestamps,
            "fps": result.fps,
            "duration": result.duration,
        }
    except FrameExtractionError as exc:
        logger.error("extract_frames_task_error", video_id=video_id, error=str(exc))
        raise self.retry(exc=exc) from exc


# ── W-02-B: Audio transcription ────────────────────────────────────────────────


@shared_task(
    bind=True,
    name="app.workers.video_tasks.transcribe_audio_task",
    max_retries=3,
    default_retry_delay=30,
)
def transcribe_audio_task(
    self,
    video_id: str,
    s3_key: str,
    language: str | None = None,
) -> dict[str, Any]:
    """
    Download video from S3 to a temp file and transcribe via T-02 AudioTranscriber.

    Returns:
        {"text": str, "segments": [...], "language": str, "error": str | None}
    """
    logger.info("transcribe_audio_task_start", video_id=video_id)

    # Download S3 object to a temp file for FFmpeg
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".mp4")
    os.close(tmp_fd)
    try:
        _s3_client().download_file(settings.S3_BUCKET_NAME, s3_key, tmp_path)
        result = asyncio.run(transcribe_audio(tmp_path, language=language))
        logger.info(
            "transcribe_audio_task_done",
            video_id=video_id,
            text_len=len(result.text),
            error=result.error,
        )
        return {
            "text": result.text,
            "segments": [s.model_dump() for s in result.segments],
            "language": result.language,
            "error": result.error,
        }
    except Exception as exc:
        logger.error("transcribe_audio_task_error", video_id=video_id, error=str(exc))
        raise self.retry(exc=exc) from exc
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ── W-02-C: Thumbnail generation ───────────────────────────────────────────────


@shared_task(
    bind=True,
    name="app.workers.video_tasks.generate_thumbnail_task",
    max_retries=2,
    default_retry_delay=15,
)
def generate_thumbnail_task(self, video_id: str, s3_key: str) -> str | None:
    """
    Generate a JPEG thumbnail from the video's first keyframe using FFmpeg
    and upload it to S3.

    Returns:
        The S3 key of the thumbnail, or None on failure.
    """
    logger.info("generate_thumbnail_task_start", video_id=video_id)
    tmp_video_fd, tmp_video = tempfile.mkstemp(suffix=".mp4")
    tmp_thumb_fd, tmp_thumb = tempfile.mkstemp(suffix=".jpg")
    os.close(tmp_video_fd)
    os.close(tmp_thumb_fd)

    try:
        _s3_client().download_file(settings.S3_BUCKET_NAME, s3_key, tmp_video)

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            tmp_video,
            "-vframes",
            "1",
            "-an",
            "-q:v",
            "2",
            tmp_thumb,
        ]
        proc = subprocess.run(cmd, capture_output=True, timeout=60, check=False)
        if proc.returncode != 0:
            err = proc.stderr.decode("utf-8", errors="replace")
            logger.warning("generate_thumbnail_ffmpeg_failed", video_id=video_id, error=err)
            return None

        thumb_key = f"thumbnails/{video_id}.jpg"
        _s3_client().upload_file(tmp_thumb, settings.S3_BUCKET_NAME, thumb_key)

        # Persist thumbnail key on the video row
        with sync_session() as db:
            video = db.get(Video, uuid.UUID(video_id))
            if video:
                video.thumbnail_s3_key = thumb_key
                video.updated_at = datetime.now(UTC)

        logger.info("generate_thumbnail_task_done", video_id=video_id, thumb_key=thumb_key)
        return thumb_key

    except Exception as exc:
        logger.error("generate_thumbnail_task_error", video_id=video_id, error=str(exc))
        raise self.retry(exc=exc) from exc
    finally:
        for p in (tmp_video, tmp_thumb):
            if os.path.exists(p):
                os.unlink(p)


# ── W-02-D: Full AI analysis pipeline ─────────────────────────────────────────


@shared_task(
    bind=True,
    name="app.workers.video_tasks.run_analysis_pipeline_task",
    max_retries=2,
    default_retry_delay=60,
)
def run_analysis_pipeline_task(
    self,
    video_id: str,
    s3_key: str,
    policy_rules: list[dict[str, Any]] | None = None,
    frames: list[str] | None = None,
    transcript: str | None = None,
) -> dict[str, Any]:
    """
    Invoke the LangGraph video analysis pipeline (C-04) and persist the result.

    Writes / updates a ModerationResult row for the given video.

    Returns:
        The ModerationReport as a dict.
    """
    logger.info("run_analysis_pipeline_task_start", video_id=video_id)

    try:
        report = asyncio.run(
            run_video_analysis(
                video_id=video_id,
                video_url=_s3_url(s3_key),
                policy_rules=policy_rules or [],
                frames=frames,
                transcript=transcript,
            )
        )
    except Exception as exc:
        logger.error("run_analysis_pipeline_task_error", video_id=video_id, error=str(exc))
        _set_video_status(video_id, VideoStatus.FAILED, error=str(exc))
        raise self.retry(exc=exc) from exc

    # Map AI decision to final autonomous status — no human gate.
    # ESCALATED = high-confidence violation → auto-reject.
    # NEEDS_REVIEW = low-confidence → auto-flag (visible in audit log but not blocked).
    # The queue is an audit log; human override is an optional exception path.
    _DECISION_TO_STATUS: dict[str, ModerationStatus] = {
        "approved": ModerationStatus.APPROVED,
        "rejected": ModerationStatus.REJECTED,
        "escalated": ModerationStatus.REJECTED,  # certain enough violation → auto-reject
        "needs_review": ModerationStatus.FLAGGED,  # uncertain → auto-flag, not blocked
    }
    mod_status = _DECISION_TO_STATUS.get(report.decision.value, ModerationStatus.FLAGGED)

    with sync_session() as db:
        existing = (
            db.query(ModerationResult)
            .filter(ModerationResult.video_id == uuid.UUID(video_id))
            .first()
        )
        # Build full justification: content summary + AI reasoning + policy triggers
        justification_parts = []
        if report.content_summary:
            justification_parts.append(report.content_summary)
        if report.reasoning:
            justification_parts.append(f"AI Reasoning: {report.reasoning}")
        if report.policy_triggers:
            justification_parts.append(f"Policy Triggers: {', '.join(report.policy_triggers)}")
        full_summary = "\n\n".join(justification_parts)

        # Violations include per-finding descriptions from the AI
        violations_data = [v.model_dump() for v in report.violations]

        if existing:
            existing.status = mod_status
            existing.overall_confidence = report.confidence
            existing.violations = violations_data
            existing.summary = full_summary
            existing.ai_model = settings.OPENAI_MODEL
            existing.updated_at = datetime.now(UTC)
            mod_result = existing
        else:
            mod_result = ModerationResult(
                video_id=uuid.UUID(video_id),
                status=mod_status,
                overall_confidence=report.confidence,
                violations=violations_data,
                summary=full_summary,
                ai_model=settings.OPENAI_MODEL,
            )
            db.add(mod_result)
            # Flush immediately so mod_result.id is populated (autoflush=False)
            db.flush()

        # Mark video as ready and capture fields before session closes
        video = db.get(Video, uuid.UUID(video_id))
        tenant_id: str | None = None
        video_owner_id: str | None = None
        video_title: str = video_id
        if video:
            video.status = VideoStatus.READY
            video.updated_at = datetime.now(UTC)
            tenant_id = video.tenant_id
            video_owner_id = str(video.owner_id)
            video_title = video.title

        result_id = str(mod_result.id)

        # Record analytics events so stats are populated
        today_str = datetime.now(UTC).strftime("%Y-%m-%d")
        db.add(
            AnalyticsEvent(
                event_type=EventType.VIDEO_PROCESSED,
                video_id=uuid.UUID(video_id),
                tenant_id=tenant_id,
                event_date=today_str,
            )
        )
        for v in report.violations:
            db.add(
                AnalyticsEvent(
                    event_type=EventType.VIOLATION_DETECTED,
                    video_id=uuid.UUID(video_id),
                    tenant_id=tenant_id,
                    category=v.category,
                    confidence=v.confidence,
                    event_date=today_str,
                )
            )

    # Always record every AI decision in the moderation queue as an audit log entry.
    # Priority reflects severity: rejected/flagged float to the top.
    from app.workers.moderation_tasks import record_moderation_decision_task

    priority = (
        2
        if mod_status == ModerationStatus.REJECTED
        else 1
        if mod_status == ModerationStatus.FLAGGED
        else 0
    )
    record_moderation_decision_task.delay(
        video_id=video_id,
        moderation_result_id=result_id,
        final_status=mod_status.value,
        priority=priority,
        tenant_id=tenant_id,
    )

    # ── Notifications ──────────────────────────────────────────────────────────
    # Fetch video title and owner_id for personalised notification content.
    _notify_moderation_complete(
        video_id=video_id,
        owner_id=video_owner_id,
        video_title=video_title,
        mod_status=mod_status,
        violations_data=violations_data,
        tenant_id=tenant_id,
    )

    logger.info(
        "run_analysis_pipeline_task_done",
        video_id=video_id,
        decision=report.decision.value,
        confidence=report.confidence,
    )
    return report.model_dump()


def _notify_moderation_complete(
    video_id: str,
    owner_id: str | None,
    video_title: str,
    mod_status: ModerationStatus,
    violations_data: list[dict],
    tenant_id: str | None,
) -> None:
    """Fire email + in-app + (if flagged/rejected) WhatsApp to the video owner."""
    if not owner_id:
        return

    from app.services.notification_dispatcher import dispatch_sync

    is_violation = mod_status in (ModerationStatus.FLAGGED, ModerationStatus.REJECTED)

    channels = ["email", "in_app"]
    if is_violation:
        channels.append("whatsapp")

    if is_violation:
        first_violation = violations_data[0] if violations_data else {}
        event_type = "moderation.flagged"
        priority = "critical" if mod_status == ModerationStatus.REJECTED else "high"
        title = (
            f"Content rejected — {video_title}"
            if mod_status == ModerationStatus.REJECTED
            else f"Content flagged — {video_title}"
        )
        message = (
            f"Your video \"{video_title}\" was {'rejected' if mod_status == ModerationStatus.REJECTED else 'flagged'} "
            f"for policy violation: {first_violation.get('category', 'policy violation')}."
        )
        extra = {
            "video_title": video_title,
            "status": mod_status.value,
            "violation_type": first_violation.get("category", "unknown"),
            "severity": "high" if mod_status == ModerationStatus.REJECTED else "medium",
            "video_id": video_id,
        }
    else:
        event_type = "moderation.complete"
        priority = "medium"
        title = f"Moderation complete — {video_title}"
        message = f'Your video "{video_title}" has been reviewed and approved.'
        extra = {
            "video_title": video_title,
            "status": mod_status.value,
            "video_id": video_id,
        }

    dispatch_sync(
        user_id=owner_id,
        channels=channels,
        event_type=event_type,
        title=title,
        message=message,
        priority=priority,
        extra=extra,
        tenant_id=tenant_id,
    )


# ── W-02-E: URL video ingestion ───────────────────────────────────────────────


@shared_task(
    bind=True,
    name="app.workers.video_tasks.process_url_video_task",
    max_retries=2,
    default_retry_delay=60,
)
def process_url_video_task(
    self,
    video_id: str,
    source_url: str,
    policy_rules: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Download a web/YouTube video via yt-dlp, upload it to S3, and run the
    full AI analysis pipeline exactly like a regular uploaded video.

    The original URL is preserved on the Video record (source_url).
    Only the video file is stored in S3; the thumbnail is taken from the
    platform's own thumbnail if available, otherwise generated by FFmpeg.
    """
    import yt_dlp

    logger.info("process_url_video_task_start", video_id=video_id, source_url=source_url)
    _set_video_status(video_id, VideoStatus.PROCESSING)

    tmp_video_path: str | None = None
    tmp_thumb_path: str | None = None

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            ydl_opts = {
                "format": "best[ext=mp4]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best",
                "outtmpl": os.path.join(tmpdir, "%(id)s.%(ext)s"),
                "quiet": True,
                "no_warnings": True,
                "writethumbnail": True,
                "socket_timeout": 30,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(source_url, download=True)

            if not info:
                raise RuntimeError("yt-dlp returned no info for URL")

            # Locate the downloaded video file
            video_filename = ydl.prepare_filename(info)
            if not os.path.exists(video_filename):
                # Try common fallback extensions
                for ext in ("mp4", "mkv", "webm"):
                    candidate = os.path.splitext(video_filename)[0] + f".{ext}"
                    if os.path.exists(candidate):
                        video_filename = candidate
                        break

            if not os.path.exists(video_filename):
                raise RuntimeError(f"Downloaded video file not found: {video_filename}")

            tmp_video_path = video_filename
            video_title: str = info.get("title") or os.path.basename(source_url)
            duration: float | None = info.get("duration")
            file_size: int = os.path.getsize(tmp_video_path)

            # Upload video to S3
            s3_key = f"url-videos/{video_id}/video{os.path.splitext(tmp_video_path)[1]}"
            with open(tmp_video_path, "rb") as fh:
                _s3_client().upload_fileobj(
                    fh,
                    settings.S3_BUCKET_NAME,
                    s3_key,
                    ExtraArgs={"ContentType": "video/mp4"},
                )
            logger.info("process_url_video_s3_upload_done", video_id=video_id, s3_key=s3_key)

            # Upload thumbnail — prefer platform thumbnail, fall back to FFmpeg
            thumb_key: str | None = None
            thumb_candidates = [
                f
                for f in os.listdir(tmpdir)
                if f.startswith(info.get("id", ""))
                and f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
            ]
            if thumb_candidates:
                thumb_src = os.path.join(tmpdir, thumb_candidates[0])
                thumb_key = f"thumbnails/{video_id}.jpg"
                with open(thumb_src, "rb") as fh:
                    _s3_client().upload_fileobj(
                        fh,
                        settings.S3_BUCKET_NAME,
                        thumb_key,
                        ExtraArgs={"ContentType": "image/jpeg"},
                    )
            else:
                # Generate via FFmpeg as fallback
                tmp_thumb_fd, tmp_thumb_path = tempfile.mkstemp(suffix=".jpg")
                os.close(tmp_thumb_fd)
                cmd = [
                    "ffmpeg",
                    "-y",
                    "-i",
                    tmp_video_path,
                    "-vframes",
                    "1",
                    "-an",
                    "-q:v",
                    "2",
                    tmp_thumb_path,
                ]
                proc = subprocess.run(cmd, capture_output=True, timeout=60, check=False)
                if proc.returncode == 0:
                    thumb_key = f"thumbnails/{video_id}.jpg"
                    _s3_client().upload_file(tmp_thumb_path, settings.S3_BUCKET_NAME, thumb_key)

            # Persist metadata on the Video record
            with sync_session() as db:
                video = db.get(Video, uuid.UUID(video_id))
                if video:
                    video.title = video_title
                    video.s3_key = s3_key
                    video.thumbnail_s3_key = thumb_key
                    video.duration_seconds = duration
                    video.file_size_bytes = file_size
                    video.content_type = "video/mp4"
                    video.updated_at = datetime.now(UTC)

            logger.info(
                "process_url_video_metadata_saved",
                video_id=video_id,
                title=video_title,
                s3_key=s3_key,
            )

            # Hand off to the standard AI analysis pipeline
            result = run_analysis_pipeline_task(
                video_id,
                s3_key,
                policy_rules=policy_rules,
            )

            logger.info("process_url_video_task_done", video_id=video_id)
            return result

    except Exception as exc:
        logger.error("process_url_video_task_error", video_id=video_id, error=str(exc))
        _set_video_status(video_id, VideoStatus.FAILED, error=str(exc))
        raise self.retry(exc=exc) from exc
    finally:
        if tmp_thumb_path and os.path.exists(tmp_thumb_path):
            os.unlink(tmp_thumb_path)


# ── W-02-G: Orchestrating entry point ─────────────────────────────────────────


@shared_task(
    bind=True,
    name="app.workers.video_tasks.process_video",
    max_retries=1,
    default_retry_delay=120,
)
def process_video(
    self,
    video_id: str,
    s3_key: str,
    policy_rules: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Orchestrate the full video processing pipeline.

    Steps (sequential to share extracted artefacts):
        1. Mark video as PROCESSING
        2. Extract frames
        3. Transcribe audio
        4. Generate thumbnail
        5. Run full AI analysis pipeline

    Args:
        video_id:     UUID string of the video.
        s3_key:       S3 object key of the uploaded video file.
        policy_rules: Active policy rule dicts passed to the AI pipeline.

    Returns:
        The ModerationReport dict from the pipeline.
    """
    logger.info("process_video_start", video_id=video_id, s3_key=s3_key)
    _set_video_status(video_id, VideoStatus.PROCESSING)

    try:
        # Step 1 — frames
        frame_data: dict[str, Any] = extract_frames_task(video_id, s3_key)
        frames: list[str] = frame_data.get("frames", [])

        # Step 2 — transcript
        transcript_data: dict[str, Any] = transcribe_audio_task(video_id, s3_key)
        transcript: str = transcript_data.get("text", "")

        # Step 3 — thumbnail (best-effort; don't fail pipeline on error)
        try:
            generate_thumbnail_task(video_id, s3_key)
        except Exception as exc:
            logger.warning("process_video_thumbnail_failed", video_id=video_id, error=str(exc))

        # Step 4 — full AI analysis
        result = run_analysis_pipeline_task(
            video_id,
            s3_key,
            policy_rules=policy_rules,
            frames=frames,
            transcript=transcript,
        )

        logger.info("process_video_done", video_id=video_id)
        return result

    except Exception as exc:
        logger.error("process_video_failed", video_id=video_id, error=str(exc))
        _set_video_status(video_id, VideoStatus.FAILED, error=str(exc))
        raise self.retry(exc=exc) from exc
