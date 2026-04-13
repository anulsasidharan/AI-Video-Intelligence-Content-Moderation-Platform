"""
W-05 Cleanup Tasks

Periodic housekeeping tasks that run on the `cleanup` queue.
Designed to be scheduled via Celery Beat or triggered manually.

Tasks:
- cleanup_temp_frames_task     — deletes S3 temp/frame artifacts beyond TTL
- purge_stale_jobs_task        — marks stuck PROCESSING videos as FAILED
- prune_old_analytics_events_task — removes analytics events beyond retention window
- cleanup_orphaned_s3_objects_task — removes S3 objects with no DB record

Schedule example (Celery Beat):
    CELERYBEAT_SCHEDULE = {
        "cleanup-temp-frames-hourly": {
            "task": "app.workers.cleanup_tasks.cleanup_temp_frames_task",
            "schedule": crontab(minute=0),          # every hour
        },
        "purge-stale-jobs-hourly": {
            "task": "app.workers.cleanup_tasks.purge_stale_jobs_task",
            "schedule": crontab(minute=30),         # every hour at :30
        },
        "prune-analytics-daily": {
            "task": "app.workers.cleanup_tasks.prune_old_analytics_events_task",
            "schedule": crontab(hour=2, minute=0),  # 02:00 UTC daily
        },
    }
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import boto3
import structlog
from celery import shared_task

from app.config import settings
from app.models.analytics import AnalyticsEvent
from app.models.video import Video, VideoStatus
from app.workers.celery_app import sync_session

logger = structlog.get_logger(__name__)

# How long (hours) a video may stay in PROCESSING before being marked stale
_STALE_PROCESSING_HOURS = 2

# S3 prefix where temporary frame artifacts are stored
_TEMP_FRAMES_PREFIX = "temp/frames/"


# ── W-05-A: Delete temp frame artifacts from S3 ───────────────────────────────


@shared_task(
    bind=True,
    name="app.workers.cleanup_tasks.cleanup_temp_frames_task",
    max_retries=2,
    default_retry_delay=60,
)
def cleanup_temp_frames_task(
    self,
    ttl_hours: int = 24,
) -> dict[str, Any]:
    """
    Delete temporary frame artifacts from S3 that are older than `ttl_hours`.

    Frame artifacts are written under the `temp/frames/` prefix during video
    analysis and are no longer needed once the pipeline completes.

    Args:
        ttl_hours: Minimum age (in hours) for an object to be eligible for deletion.

    Returns:
        {"deleted": int, "errors": int}
    """
    logger.info("cleanup_temp_frames_start", ttl_hours=ttl_hours)

    cutoff = datetime.now(UTC) - timedelta(hours=ttl_hours)
    deleted = errors = 0

    try:
        s3 = boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
        )

        paginator = s3.get_paginator("list_objects_v2")
        pages = paginator.paginate(
            Bucket=settings.S3_BUCKET_NAME,
            Prefix=_TEMP_FRAMES_PREFIX,
        )

        keys_to_delete: list[dict] = []
        for page in pages:
            for obj in page.get("Contents", []):
                if obj["LastModified"] < cutoff:
                    keys_to_delete.append({"Key": obj["Key"]})

        # S3 batch delete — max 1 000 per request
        batch_size = 1000
        for i in range(0, len(keys_to_delete), batch_size):
            batch = keys_to_delete[i : i + batch_size]
            resp = s3.delete_objects(
                Bucket=settings.S3_BUCKET_NAME,
                Delete={"Objects": batch, "Quiet": True},
            )
            errors += len(resp.get("Errors", []))
            deleted += len(batch) - len(resp.get("Errors", []))

    except Exception as exc:
        logger.error("cleanup_temp_frames_error", error=str(exc))
        raise self.retry(exc=exc) from exc

    logger.info("cleanup_temp_frames_done", deleted=deleted, errors=errors)
    return {"deleted": deleted, "errors": errors}


# ── W-05-B: Purge stale jobs ──────────────────────────────────────────────────


@shared_task(
    bind=True,
    name="app.workers.cleanup_tasks.purge_stale_jobs_task",
    max_retries=3,
    default_retry_delay=60,
)
def purge_stale_jobs_task(
    self,
    stale_hours: int = _STALE_PROCESSING_HOURS,
) -> dict[str, Any]:
    """
    Find videos stuck in PROCESSING status beyond `stale_hours` and mark
    them FAILED so they do not clog the pipeline or moderation queue.

    Args:
        stale_hours: Age threshold in hours (default 2).

    Returns:
        {"marked_failed": int}
    """
    logger.info("purge_stale_jobs_start", stale_hours=stale_hours)

    cutoff = datetime.now(UTC) - timedelta(hours=stale_hours)
    marked_failed = 0

    try:
        with sync_session() as db:
            stale_videos = (
                db.query(Video)
                .filter(
                    Video.status == VideoStatus.PROCESSING,
                    Video.updated_at < cutoff,
                )
                .all()
            )
            for video in stale_videos:
                video.status = VideoStatus.FAILED
                video.error_message = (
                    f"Processing timed out after {stale_hours}h — marked failed by cleanup task."
                )
                video.updated_at = datetime.now(UTC)
                marked_failed += 1

    except Exception as exc:
        logger.error("purge_stale_jobs_error", error=str(exc))
        raise self.retry(exc=exc) from exc

    logger.info("purge_stale_jobs_done", marked_failed=marked_failed)
    return {"marked_failed": marked_failed}


# ── W-05-C: Prune old analytics events ───────────────────────────────────────


@shared_task(
    bind=True,
    name="app.workers.cleanup_tasks.prune_old_analytics_events_task",
    max_retries=3,
    default_retry_delay=60,
)
def prune_old_analytics_events_task(
    self,
    retention_days: int = 90,
) -> dict[str, Any]:
    """
    Delete analytics_events rows older than `retention_days`.

    Args:
        retention_days: Events older than this are deleted (default 90 days).

    Returns:
        {"deleted": int}
    """
    logger.info("prune_old_analytics_events_start", retention_days=retention_days)

    cutoff_date = (datetime.now(UTC) - timedelta(days=retention_days)).date().isoformat()
    deleted = 0

    try:
        with sync_session() as db:
            deleted = (
                db.query(AnalyticsEvent)
                .filter(AnalyticsEvent.event_date < cutoff_date)
                .delete(synchronize_session=False)
            )

    except Exception as exc:
        logger.error("prune_old_analytics_events_error", error=str(exc))
        raise self.retry(exc=exc) from exc

    logger.info("prune_old_analytics_events_done", deleted=deleted, cutoff_date=cutoff_date)
    return {"deleted": deleted}


# ── W-05-D: Clean up orphaned S3 objects ──────────────────────────────────────


@shared_task(
    bind=True,
    name="app.workers.cleanup_tasks.cleanup_orphaned_s3_objects_task",
    max_retries=2,
    default_retry_delay=120,
)
def cleanup_orphaned_s3_objects_task(
    self,
    prefix: str = "videos/",
    min_age_hours: int = 48,
) -> dict[str, Any]:
    """
    Scan the S3 bucket under `prefix` and delete objects that have no
    corresponding Video row in the database (i.e. orphaned uploads).

    Objects younger than `min_age_hours` are skipped to avoid deleting
    in-progress uploads that have not yet been registered.

    Args:
        prefix:        S3 prefix to scan (default "videos/").
        min_age_hours: Minimum object age before orphan check (default 48 h).

    Returns:
        {"scanned": int, "deleted": int, "errors": int}
    """
    logger.info("cleanup_orphaned_s3_start", prefix=prefix, min_age_hours=min_age_hours)

    cutoff = datetime.now(UTC) - timedelta(hours=min_age_hours)
    scanned = deleted = errors = 0

    try:
        s3 = boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
        )

        paginator = s3.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=settings.S3_BUCKET_NAME, Prefix=prefix)

        orphan_keys: list[dict] = []
        for page in pages:
            for obj in page.get("Contents", []):
                scanned += 1
                if obj["LastModified"] >= cutoff:
                    continue

                s3_key = obj["Key"]
                with sync_session() as db:
                    exists = db.query(Video).filter(Video.s3_key == s3_key).first()
                if not exists:
                    orphan_keys.append({"Key": s3_key})

        batch_size = 1000
        for i in range(0, len(orphan_keys), batch_size):
            batch = orphan_keys[i : i + batch_size]
            resp = s3.delete_objects(
                Bucket=settings.S3_BUCKET_NAME,
                Delete={"Objects": batch, "Quiet": True},
            )
            batch_errors = len(resp.get("Errors", []))
            errors += batch_errors
            deleted += len(batch) - batch_errors

    except Exception as exc:
        logger.error("cleanup_orphaned_s3_error", error=str(exc))
        raise self.retry(exc=exc) from exc

    logger.info(
        "cleanup_orphaned_s3_done",
        scanned=scanned,
        deleted=deleted,
        errors=errors,
    )
    return {"scanned": scanned, "deleted": deleted, "errors": errors}
