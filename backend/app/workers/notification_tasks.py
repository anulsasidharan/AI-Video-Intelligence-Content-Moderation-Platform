"""
W-05 Notification Tasks

Celery tasks for async delivery of email, in-app, and WhatsApp notifications.

Entry points:
    send_email_notification_task.delay(notification_id, to_email, event_type, ...)
    send_whatsapp_notification_task.delay(notification_id, to_number, event_type, ...)
    send_inapp_notification_task.delay(notification_id, user_id)
    process_notification_batch_task.delay(user_id, channel, event_type)
    send_daily_digest_task.delay(user_id)
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import structlog
from celery import shared_task

from app.models.notification import NotificationStatus
from app.workers.celery_app import sync_session

logger = structlog.get_logger(__name__)


# ── W-05-A: Email delivery ─────────────────────────────────────────────────────


@shared_task(
    bind=True,
    name="app.workers.notification_tasks.send_email_notification_task",
    max_retries=3,
    default_retry_delay=60,
)
def send_email_notification_task(
    self,
    notification_id: str,
    to_email: str,
    event_type: str,
    user_name: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Deliver a notification via email (SendGrid).

    Reads the Notification row identified by notification_id, dispatches
    the appropriate email helper based on event_type, and updates delivery
    status + metadata on success or failure.

    Args:
        notification_id: UUID string of the Notification row.
        to_email:         Recipient email address.
        event_type:       e.g. "moderation.complete", "moderation.flagged".
        user_name:        Recipient display name for personalisation.
        extra:            Additional context (video_title, violation_type, …).
    """
    from app.services.email_service import EmailService

    extra = extra or {}
    svc = EmailService()
    logger.info("send_email_task_start", notification_id=notification_id, event_type=event_type)

    try:
        result: dict[str, Any]

        if event_type == "moderation.complete":
            result = svc.send_moderation_complete(
                to_email=to_email,
                user_name=user_name,
                video_title=extra.get("video_title", "your video"),
                status=extra.get("status", "pending"),
                report_url=extra.get("report_url"),
            )
        elif event_type in ("moderation.flagged", "policy.violation"):
            result = svc.send_content_flagged(
                to_email=to_email,
                user_name=user_name,
                video_title=extra.get("video_title", "your video"),
                violation_type=extra.get("violation_type", "unknown"),
                severity=extra.get("severity", "medium"),
            )
        elif event_type in ("system.quota_warning", "system.api_error"):
            result = svc.send_system_alert(
                to_email=to_email,
                user_name=user_name,
                alert_type=event_type,
                details=extra.get("details", "Please check your VidShield dashboard."),
            )
        elif event_type == "user.registered":
            result = svc.send_welcome(
                to_email=to_email,
                user_name=user_name,
            )
        elif event_type == "user.password_changed":
            result = svc.send_password_changed(
                to_email=to_email,
                user_name=user_name,
            )
        else:
            # Generic send for unsupported event types
            result = svc.send(
                to_email=to_email,
                subject=extra.get("title", f"[VidShield] {event_type}"),
                html_body=f"<p>{extra.get('message', '')}</p>",
                plain_body=extra.get("message", ""),
            )

        _mark_sent(notification_id, metadata=result)
        logger.info("send_email_task_done", notification_id=notification_id, **result)
        return result

    except Exception as exc:
        logger.error("send_email_task_failed", notification_id=notification_id, error=str(exc))
        _mark_failed(notification_id)
        raise self.retry(exc=exc) from exc


# ── W-05-B: WhatsApp delivery ──────────────────────────────────────────────────


@shared_task(
    bind=True,
    name="app.workers.notification_tasks.send_whatsapp_notification_task",
    max_retries=3,
    default_retry_delay=60,
)
def send_whatsapp_notification_task(
    self,
    notification_id: str,
    to_number: str,
    event_type: str,
    user_name: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Deliver a notification via WhatsApp (Twilio).

    Args:
        notification_id: UUID string of the Notification row.
        to_number:        Recipient phone number in E.164 format.
        event_type:       e.g. "moderation.flagged", "stream.alert".
        user_name:        Recipient display name.
        extra:            Additional context passed to the template helper.
    """
    from app.services.whatsapp_service import WhatsAppService

    extra = extra or {}
    svc = WhatsAppService()
    logger.info(
        "send_whatsapp_task_start",
        notification_id=notification_id,
        event_type=event_type,
    )

    try:
        result: dict[str, Any]

        if event_type == "moderation.complete":
            result = svc.send_moderation_complete(
                to_number=to_number,
                user_name=user_name,
                video_title=extra.get("video_title", "your video"),
                status=extra.get("status", "pending"),
            )
        elif event_type in ("moderation.flagged", "policy.violation"):
            result = svc.send_content_flagged(
                to_number=to_number,
                user_name=user_name,
                video_title=extra.get("video_title", "your video"),
                violation_type=extra.get("violation_type", "unknown"),
                severity=extra.get("severity", "medium"),
            )
        elif event_type == "stream.alert":
            result = svc.send_stream_alert(
                to_number=to_number,
                stream_title=extra.get("stream_title", "your stream"),
                category=extra.get("category", "unknown"),
                severity=extra.get("severity", "medium"),
                confidence=float(extra.get("confidence", 0.0)),
            )
        elif event_type in ("system.quota_warning", "system.api_error"):
            result = svc.send_system_alert(
                to_number=to_number,
                alert_type=event_type,
                details=extra.get("details", "Check your VidShield dashboard."),
            )
        elif event_type == "user.registered":
            result = svc.send_welcome(
                to_number=to_number,
                user_name=user_name,
            )
        elif event_type == "user.password_changed":
            result = svc.send_password_changed(
                to_number=to_number,
                user_name=user_name,
            )
        else:
            result = svc.send(
                to_number=to_number,
                body=extra.get("message", f"[VidShield] {event_type}"),
            )

        _mark_sent(notification_id, metadata=result)
        logger.info("send_whatsapp_task_done", notification_id=notification_id, **result)
        return result

    except Exception as exc:
        logger.error("send_whatsapp_task_failed", notification_id=notification_id, error=str(exc))
        _mark_failed(notification_id)
        raise self.retry(exc=exc) from exc


# ── W-05-C: In-app delivery ────────────────────────────────────────────────────


@shared_task(
    bind=True,
    name="app.workers.notification_tasks.send_inapp_notification_task",
    max_retries=2,
    default_retry_delay=10,
)
def send_inapp_notification_task(
    self,
    notification_id: str,
    user_id: str,
) -> dict[str, Any]:
    """
    Mark an in-app Notification row as sent and push a real-time Socket.IO
    event to the user's private room ({user_id}).

    The Socket.IO server instance is accessed via the `main` module so that
    the same sio object used by the API is reused here.

    Args:
        notification_id: UUID string of the Notification row.
        user_id:         UUID string of the recipient user.
    """
    import asyncio

    from app.models.notification import Notification

    logger.info("send_inapp_task_start", notification_id=notification_id, user_id=user_id)

    try:
        notif_dict: dict[str, Any] = {}

        with sync_session() as db:
            notif = db.get(Notification, uuid.UUID(notification_id))
            if not notif:
                logger.warning("send_inapp_task_not_found", notification_id=notification_id)
                return {"skipped": True}

            notif.status = NotificationStatus.SENT
            notif.sent_at = datetime.now(UTC)
            db.flush()

            notif_dict = {
                "id": str(notif.id),
                "event_type": notif.event_type,
                "priority": notif.priority,
                "title": notif.title,
                "message": notif.message,
                "data": notif.data,
                "created_at": notif.created_at.isoformat(),
            }

        # Push via Socket.IO to the user's private room
        try:
            from app.main import sio

            asyncio.run(
                sio.emit(
                    "notification",
                    notif_dict,
                    room=user_id,
                )
            )
        except Exception as sio_exc:
            # Non-fatal: notification is already persisted; real-time push may
            # fail when the worker process doesn't have a live event loop.
            logger.warning(
                "send_inapp_socketio_failed",
                notification_id=notification_id,
                error=str(sio_exc),
            )

        logger.info("send_inapp_task_done", notification_id=notification_id)
        return {"notification_id": notification_id, "user_id": user_id}

    except Exception as exc:
        logger.error("send_inapp_task_failed", notification_id=notification_id, error=str(exc))
        raise self.retry(exc=exc) from exc


# ── W-05-D: Batch aggregation ─────────────────────────────────────────────────


@shared_task(
    bind=True,
    name="app.workers.notification_tasks.process_notification_batch_task",
    max_retries=2,
    default_retry_delay=30,
)
def process_notification_batch_task(
    self,
    user_id: str,
    channel: str,
    event_type: str,
) -> dict[str, Any]:
    """
    Aggregate all PENDING notifications for a user/channel/event_type
    combination and dispatch a single batched delivery.

    Used when a user has configured frequency=batched for a preference.

    Returns:
        {"batched": int, "dispatched": bool}
    """
    from sqlalchemy import and_

    from app.models.notification import (
        Notification,
        NotificationChannel,
        NotificationStatus,
    )

    logger.info(
        "batch_notification_task_start",
        user_id=user_id,
        channel=channel,
        event_type=event_type,
    )

    try:
        channel_enum = NotificationChannel(channel)
        pending_ids: list[str] = []

        with sync_session() as db:
            rows = (
                db.query(Notification)
                .filter(
                    and_(
                        Notification.user_id == uuid.UUID(user_id),
                        Notification.channel == channel_enum,
                        Notification.event_type == event_type,
                        Notification.status == NotificationStatus.PENDING,
                    )
                )
                .all()
            )
            pending_ids = [str(r.id) for r in rows]

        if not pending_ids:
            return {"batched": 0, "dispatched": False}

        # For batched in-app: mark all sent
        if channel == "in_app":
            for nid in pending_ids:
                send_inapp_notification_task.delay(notification_id=nid, user_id=user_id)

        logger.info(
            "batch_notification_task_done",
            batched=len(pending_ids),
            channel=channel,
        )
        return {"batched": len(pending_ids), "dispatched": True}

    except Exception as exc:
        logger.error("batch_notification_task_error", user_id=user_id, error=str(exc))
        raise self.retry(exc=exc) from exc


# ── W-05-E: Daily digest ───────────────────────────────────────────────────────


@shared_task(
    bind=True,
    name="app.workers.notification_tasks.send_daily_digest_task",
    max_retries=2,
    default_retry_delay=120,
)
def send_daily_digest_task(self, user_id: str) -> dict[str, Any]:
    """
    Compile and send a daily email digest to a user who opted in.

    Aggregates ModerationResult stats for the past 24 hours and sends via
    EmailService.send_daily_digest().

    Args:
        user_id: UUID string of the user to digest.

    Returns:
        {"sent": bool, "email": str}
    """
    from datetime import timedelta

    from sqlalchemy import and_, func

    from app.models.moderation import ModerationResult, ModerationStatus
    from app.models.user import User
    from app.services.email_service import EmailService

    logger.info("daily_digest_task_start", user_id=user_id)

    try:
        with sync_session() as db:
            user = db.get(User, uuid.UUID(user_id))
            if not user or not user.email:
                return {"sent": False, "email": ""}

            since = datetime.now(UTC) - timedelta(hours=24)

            def count_status(status: ModerationStatus) -> int:
                return (
                    db.query(func.count(ModerationResult.id))
                    .filter(
                        and_(
                            ModerationResult.created_at >= since,
                        )
                    )
                    .scalar()
                    or 0
                )

            total = (
                db.query(func.count(ModerationResult.id))
                .filter(ModerationResult.created_at >= since)
                .scalar()
                or 0
            )
            approved = (
                db.query(func.count(ModerationResult.id))
                .filter(
                    and_(
                        ModerationResult.created_at >= since,
                        ModerationResult.status == ModerationStatus.APPROVED,
                    )
                )
                .scalar()
                or 0
            )
            flagged = (
                db.query(func.count(ModerationResult.id))
                .filter(
                    and_(
                        ModerationResult.created_at >= since,
                        ModerationResult.status == ModerationStatus.FLAGGED,
                    )
                )
                .scalar()
                or 0
            )
            rejected = (
                db.query(func.count(ModerationResult.id))
                .filter(
                    and_(
                        ModerationResult.created_at >= since,
                        ModerationResult.status == ModerationStatus.REJECTED,
                    )
                )
                .scalar()
                or 0
            )

        stats = {
            "total": total,
            "approved": approved,
            "flagged": flagged,
            "rejected": rejected,
            "date": datetime.now(UTC).strftime("%Y-%m-%d"),
        }

        svc = EmailService()
        svc.send_daily_digest(
            to_email=user.email,
            user_name=user.name or user.email,
            stats=stats,
        )

        logger.info("daily_digest_task_done", user_id=user_id, email=user.email)
        return {"sent": True, "email": user.email}

    except Exception as exc:
        logger.error("daily_digest_task_error", user_id=user_id, error=str(exc))
        raise self.retry(exc=exc) from exc


# ── W-05-F: Daily digest beat task ────────────────────────────────────────────


@shared_task(
    bind=True,
    name="app.workers.notification_tasks.send_daily_digests_beat_task",
    max_retries=1,
    default_retry_delay=300,
)
def send_daily_digests_beat_task(self) -> dict[str, Any]:
    """
    Celery Beat entry point — runs every 24 hours.
    Finds all users who have opted in to daily_digest frequency for email
    and enqueues a send_daily_digest_task for each.
    """
    from app.models.notification import NotificationFrequency, NotificationPreference

    logger.info("daily_digests_beat_start")
    dispatched = 0

    try:
        with sync_session() as db:
            prefs = (
                db.query(NotificationPreference)
                .filter_by(
                    frequency=NotificationFrequency.DAILY_DIGEST,
                    enabled=True,
                )
                .all()
            )
            user_ids = list({str(p.user_id) for p in prefs})

        for uid in user_ids:
            send_daily_digest_task.delay(user_id=uid)
            dispatched += 1

        logger.info("daily_digests_beat_done", dispatched=dispatched)
        return {"dispatched": dispatched}

    except Exception as exc:
        logger.error("daily_digests_beat_error", error=str(exc))
        raise self.retry(exc=exc) from exc


# ── Internal helpers ───────────────────────────────────────────────────────────


def _mark_sent(notification_id: str, metadata: dict[str, Any] | None = None) -> None:
    """Update a Notification row to SENT status."""
    from app.models.notification import Notification

    with sync_session() as db:
        notif = db.get(Notification, uuid.UUID(notification_id))
        if notif:
            notif.status = NotificationStatus.SENT
            notif.sent_at = datetime.now(UTC)
            if metadata:
                notif.delivery_meta = metadata


def _mark_failed(notification_id: str) -> None:
    """Increment retry_count and set status to FAILED."""
    from app.models.notification import Notification

    with sync_session() as db:
        notif = db.get(Notification, uuid.UUID(notification_id))
        if notif:
            notif.status = NotificationStatus.FAILED
            notif.retry_count = (notif.retry_count or 0) + 1
