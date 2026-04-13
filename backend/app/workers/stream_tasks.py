"""
W-07 Live Stream Moderation Tasks

Celery tasks for real-time frame-by-frame live stream moderation.

Entry points:
    moderate_live_chunk_task.delay(stream_id, frames_b64, transcript_hint="")

Flow:
    1. Load LiveStream from DB — bail early if moderation_active is False.
    2. Run LiveStreamModerator.analyze_chunk() (asyncio.run).
    3. For each violation → create Alert record in DB.
    4. Publish LiveChunkResult as JSON to Redis pub/sub channel
       "live:events:{stream_id}" so the WebSocket handler can forward
       it to connected browser clients in real-time.
    5. Update frames_processed counter on the LiveStream row.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any

import structlog
from celery import shared_task

from app.models.alert import Alert, AlertSeverity, LiveStream
from app.workers.celery_app import sync_session

logger = structlog.get_logger(__name__)

_SEVERITY_MAP: dict[str, AlertSeverity] = {
    "low": AlertSeverity.LOW,
    "medium": AlertSeverity.MEDIUM,
    "high": AlertSeverity.HIGH,
    "critical": AlertSeverity.CRITICAL,
}


# ── W-07-A: Moderate a single frame chunk ─────────────────────────────────────


@shared_task(
    bind=True,
    name="app.workers.stream_tasks.moderate_live_chunk_task",
    max_retries=0,  # live analysis — no retries (stale by the time it retried)
    soft_time_limit=25,  # 25 s soft limit (GPT-4o vision p95 ≈ 8 s)
    time_limit=30,
)
def moderate_live_chunk_task(
    self,
    stream_id: str,
    frames_b64: list[str],
    transcript_hint: str = "",
) -> dict[str, Any]:
    """
    Analyse a batch of frames from a live stream and persist any violations.

    Args:
        stream_id:       UUID of the LiveStream.
        frames_b64:      List of base64-encoded JPEG frames (max 10).
        transcript_hint: Short speech snippet from this chunk (optional).

    Returns:
        dict summarising the analysis result (stored as Celery task result).
    """
    from app.ai.agents.live_stream_moderator import LiveStreamModerator

    with sync_session() as db:
        stream = db.get(LiveStream, uuid.UUID(stream_id))
        if not stream:
            logger.warning("stream_not_found", stream_id=stream_id)
            return {"error": "stream_not_found"}

        if not stream.moderation_active:
            logger.info("stream_moderation_inactive", stream_id=stream_id)
            return {"skipped": "moderation_not_active"}

        # Run async agent in the sync Celery worker context
        moderator = LiveStreamModerator()
        result = asyncio.run(
            moderator.analyze_chunk(
                stream_id=stream_id,
                frames=frames_b64,
                transcript_hint=transcript_hint,
            )
        )

        # Persist violations as Alert records
        for violation in result.violations:
            severity = _SEVERITY_MAP.get(violation.severity, AlertSeverity.MEDIUM)
            alert = Alert(
                stream_id=uuid.UUID(stream_id),
                severity=severity,
                category=violation.category,
                message=violation.description,
                confidence=violation.confidence,
                tenant_id=stream.tenant_id,
            )
            db.add(alert)

        # Update frame counter
        stream.frames_processed = (stream.frames_processed or 0) + len(frames_b64)
        db.flush()

        # Publish result to Redis pub/sub → WebSocket handler picks it up
        _publish_to_redis(stream_id, result.to_ws_event())

        # If minor detected → also trigger WhatsApp/email notification to stream owner
        if result.face_analysis.has_minor and not result.face_analysis.error:
            _notify_minor_detected(db, stream, stream_id)

        logger.info(
            "live_chunk_processed",
            stream_id=stream_id,
            violations=len(result.violations),
            frames=len(frames_b64),
            overall_safe=result.overall_safe,
        )

        return {
            "stream_id": stream_id,
            "violations": len(result.violations),
            "overall_safe": result.overall_safe,
            "highest_severity": result.highest_severity,
        }


def _publish_to_redis(stream_id: str, event: dict[str, Any]) -> None:
    """Publish a moderation event to the Redis pub/sub channel for this stream."""
    try:
        import redis as sync_redis

        from app.config import settings

        r = sync_redis.from_url(settings.REDIS_URL, decode_responses=True)
        r.publish(f"live:events:{stream_id}", json.dumps(event))
        r.close()
    except Exception as exc:
        logger.error("redis_publish_failed", stream_id=stream_id, error=str(exc))


def _notify_minor_detected(db: Any, stream: LiveStream, stream_id: str) -> None:
    """Fire a high-priority notification to the stream owner when a minor is detected."""
    try:
        from app.services.notification_dispatcher import dispatch_sync

        dispatch_sync(
            user_id=str(stream.owner_id),
            channels=["in_app", "email"],
            event_type="stream.minor_detected",
            title="Minor detected in live stream",
            message=(
                f'A person under 18 was detected in your live stream "{stream.title}". '
                "Immediate review may be required."
            ),
            priority="high",
            extra={"stream_id": stream_id, "stream_title": stream.title},
        )
    except Exception as exc:
        logger.error("minor_detected_notify_failed", stream_id=stream_id, error=str(exc))
