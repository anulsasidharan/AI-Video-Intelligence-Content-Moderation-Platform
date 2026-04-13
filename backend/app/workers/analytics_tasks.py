"""
W-04 Analytics Tasks

Async metrics aggregation tasks. All computation is decoupled from the
API request path and runs in Celery workers on the `analytics` queue.

Public entry points:
    aggregate_daily_stats_task.delay(date_str="2026-03-18", tenant_id=None)
    compute_policy_effectiveness_task.delay(policy_id="...")
    flush_analytics_events_task.delay()
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from typing import Any

import structlog
from celery import shared_task
from sqlalchemy import func

from app.models.analytics import AnalyticsEvent, EventType
from app.models.moderation import ModerationResult, ModerationStatus
from app.workers.celery_app import sync_session

logger = structlog.get_logger(__name__)

# Redis key prefix for buffered analytics events
_ANALYTICS_BUFFER_KEY = "vidshield:analytics:event_buffer"


# ── W-04-A: Aggregate daily statistics ────────────────────────────────────────


@shared_task(
    bind=True,
    name="app.workers.analytics_tasks.aggregate_daily_stats_task",
    max_retries=3,
    default_retry_delay=60,
)
def aggregate_daily_stats_task(
    self,
    date_str: str | None = None,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    """
    Roll up per-day analytics metrics from the analytics_events table.

    Computes:
    - videos_processed: count of VIDEO_PROCESSED events
    - violations_detected: count of VIOLATION_DETECTED events
    - reviews_completed: count of REVIEW_COMPLETED events
    - avg_confidence: mean confidence across VIOLATION_DETECTED events

    Args:
        date_str:  ISO date string "YYYY-MM-DD". Defaults to yesterday.
        tenant_id: Scope aggregation to a single tenant. None = all tenants.

    Returns:
        Aggregation result dict.
    """
    target_date = date_str or (date.today() - timedelta(days=1)).isoformat()
    logger.info("aggregate_daily_stats_start", date=target_date, tenant_id=tenant_id)

    try:
        with sync_session() as db:
            base = db.query(AnalyticsEvent).filter(AnalyticsEvent.event_date == target_date)
            if tenant_id:
                base = base.filter(AnalyticsEvent.tenant_id == tenant_id)

            videos_processed = base.filter(
                AnalyticsEvent.event_type == EventType.VIDEO_PROCESSED
            ).count()

            violations_detected = base.filter(
                AnalyticsEvent.event_type == EventType.VIOLATION_DETECTED
            ).count()

            reviews_completed = base.filter(
                AnalyticsEvent.event_type == EventType.REVIEW_COMPLETED
            ).count()

            avg_confidence_row = db.query(func.avg(AnalyticsEvent.confidence)).filter(
                AnalyticsEvent.event_date == target_date,
                AnalyticsEvent.event_type == EventType.VIOLATION_DETECTED,
                AnalyticsEvent.confidence.isnot(None),
            )
            if tenant_id:
                avg_confidence_row = avg_confidence_row.filter(
                    AnalyticsEvent.tenant_id == tenant_id
                )
            avg_confidence = float(avg_confidence_row.scalar() or 0.0)

        result = {
            "date": target_date,
            "tenant_id": tenant_id,
            "videos_processed": videos_processed,
            "violations_detected": violations_detected,
            "reviews_completed": reviews_completed,
            "avg_confidence": round(avg_confidence, 4),
        }
        logger.info("aggregate_daily_stats_done", **result)
        return result

    except Exception as exc:
        logger.error("aggregate_daily_stats_error", date=target_date, error=str(exc))
        raise self.retry(exc=exc) from exc


# ── W-04-B: Policy effectiveness ──────────────────────────────────────────────


@shared_task(
    bind=True,
    name="app.workers.analytics_tasks.compute_policy_effectiveness_task",
    max_retries=3,
    default_retry_delay=60,
)
def compute_policy_effectiveness_task(
    self,
    policy_id: str,
) -> dict[str, Any]:
    """
    Compute effectiveness metrics for a given moderation policy.

    Metrics:
    - total_evaluated: total moderation results
    - approved: count with APPROVED status
    - rejected: count with REJECTED status
    - escalated: count with ESCALATED status
    - flagged: count with FLAGGED status
    - approval_rate: approved / total_evaluated
    - escalation_rate: escalated / total_evaluated

    Returns:
        Effectiveness metrics dict.
    """
    logger.info("compute_policy_effectiveness_start", policy_id=policy_id)

    try:
        with sync_session() as db:
            total = db.query(ModerationResult).count()

            counts: dict[str, int] = {}
            for status in (
                ModerationStatus.APPROVED,
                ModerationStatus.REJECTED,
                ModerationStatus.ESCALATED,
                ModerationStatus.FLAGGED,
            ):
                counts[status.value] = (
                    db.query(ModerationResult).filter(ModerationResult.status == status).count()
                )

        approved = counts.get("approved", 0)
        escalated = counts.get("escalated", 0)

        result = {
            "policy_id": policy_id,
            "total_evaluated": total,
            "approved": approved,
            "rejected": counts.get("rejected", 0),
            "escalated": escalated,
            "flagged": counts.get("flagged", 0),
            "approval_rate": round(approved / total, 4) if total else 0.0,
            "escalation_rate": round(escalated / total, 4) if total else 0.0,
        }
        logger.info("compute_policy_effectiveness_done", **result)
        return result

    except Exception as exc:
        logger.error("compute_policy_effectiveness_error", policy_id=policy_id, error=str(exc))
        raise self.retry(exc=exc) from exc


# ── W-04-C: Flush buffered events ─────────────────────────────────────────────


@shared_task(
    bind=True,
    name="app.workers.analytics_tasks.flush_analytics_events_task",
    max_retries=3,
    default_retry_delay=30,
)
def flush_analytics_events_task(self) -> dict[str, Any]:
    """
    Drain the Redis analytics event buffer and persist records to the
    analytics_events table in PostgreSQL.

    Events are pushed onto a Redis list (`vidshield:analytics:event_buffer`)
    by API handlers and worker tasks that need lightweight fire-and-forget
    event recording without blocking on a DB write.

    Each buffered item is a JSON string with keys:
        event_type, video_id, tenant_id, category, confidence, extra, event_date

    Returns:
        {"flushed": int, "errors": int}
    """
    import redis as redis_lib

    logger.info("flush_analytics_events_start")

    flushed = errors = 0

    try:
        r = redis_lib.from_url(
            __import__("app.config", fromlist=["settings"]).settings.REDIS_URL,
            decode_responses=True,
        )

        # Drain entire buffer in one atomic pop (up to 500 items per run)
        pipeline = r.pipeline()
        pipeline.lrange(_ANALYTICS_BUFFER_KEY, 0, 499)
        pipeline.ltrim(_ANALYTICS_BUFFER_KEY, 500, -1)
        raw_events, _ = pipeline.execute()

        events_to_insert: list[AnalyticsEvent] = []
        for raw in raw_events:
            try:
                data: dict = json.loads(raw)
                events_to_insert.append(
                    AnalyticsEvent(
                        event_type=EventType(data["event_type"]),
                        video_id=data.get("video_id"),
                        tenant_id=data.get("tenant_id"),
                        category=data.get("category"),
                        confidence=data.get("confidence"),
                        extra=(json.dumps(data.get("extra")) if data.get("extra") else None),
                        event_date=data.get("event_date", datetime.now(UTC).date().isoformat()),
                    )
                )
            except Exception as parse_exc:
                logger.warning("flush_analytics_parse_error", error=str(parse_exc), raw=raw)
                errors += 1

        if events_to_insert:
            with sync_session() as db:
                db.add_all(events_to_insert)
            flushed = len(events_to_insert)

    except Exception as exc:
        logger.error("flush_analytics_events_error", error=str(exc))
        raise self.retry(exc=exc) from exc

    logger.info("flush_analytics_events_done", flushed=flushed, errors=errors)
    return {"flushed": flushed, "errors": errors}
