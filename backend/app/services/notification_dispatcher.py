"""
Notification Dispatcher

Central helper for firing multi-channel notifications from both:
  - Celery sync tasks  → dispatch_sync(user_id, channels, ...)
  - FastAPI async routes → dispatch_async(db, user, channels, ...)

Both functions:
  1. Skip channels where the user has opted out (NotificationPreference)
  2. Skip channels where the required contact info is missing
  3. Create a Notification DB record per channel
  4. Queue the appropriate Celery delivery task

Usage from a Celery task:
    from app.services.notification_dispatcher import dispatch_sync
    dispatch_sync(
        user_id="uuid-str",
        channels=["email", "in_app"],
        event_type="moderation.complete",
        title="Moderation complete",
        message="Your video has been reviewed.",
        extra={"video_title": "My Video", "status": "approved"},
    )

Usage from a FastAPI route:
    from app.services.notification_dispatcher import dispatch_async
    await dispatch_async(
        db=db,
        user=current_user,
        channels=["email", "whatsapp"],
        event_type="user.password_changed",
        title="Password changed",
        message="Your password was updated successfully.",
    )
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import structlog

from app.models.notification import (
    Notification,
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
)

logger = structlog.get_logger(__name__)


# ── Sync dispatcher (Celery tasks) ────────────────────────────────────────────


def dispatch_sync(
    user_id: str,
    channels: list[str],
    event_type: str,
    title: str,
    message: str,
    priority: str = NotificationPriority.MEDIUM,
    extra: dict[str, Any] | None = None,
    tenant_id: str | None = None,
) -> None:
    """
    Create Notification records and queue delivery tasks for each channel.

    Designed for use inside Celery sync tasks (uses sync_session).
    Silently skips channels where the user has opted out or is missing
    contact information. Never raises — errors are logged and swallowed so
    a notification failure cannot abort the calling pipeline task.

    Args:
        user_id:    UUID string of the recipient.
        channels:   List of channel strings: "email", "in_app", "whatsapp".
        event_type: Canonical event type, e.g. "moderation.complete".
        title:      Short notification title.
        message:    Notification body text.
        priority:   One of NotificationPriority values.
        extra:      Additional payload forwarded to the delivery task.
        tenant_id:  Optional tenant scope.
    """
    from app.models.notification import NotificationPreference
    from app.models.user import User
    from app.workers.celery_app import sync_session
    from app.workers.notification_tasks import (
        send_email_notification_task,
        send_inapp_notification_task,
        send_whatsapp_notification_task,
    )

    extra = extra or {}

    try:
        with sync_session() as db:
            user = db.get(User, uuid.UUID(user_id))
            if not user:
                logger.warning("dispatch_sync_user_not_found", user_id=user_id)
                return

            for channel_str in channels:
                try:
                    channel = NotificationChannel(channel_str)
                except ValueError:
                    logger.warning("dispatch_sync_unknown_channel", channel=channel_str)
                    continue

                # Skip if missing contact info
                if channel == NotificationChannel.EMAIL and not user.email:
                    continue
                if channel == NotificationChannel.WHATSAPP and not user.whatsapp_number:
                    continue

                # Check preference opt-out
                pref = (
                    db.query(NotificationPreference)
                    .filter_by(
                        user_id=user.id,
                        channel=channel,
                        event_type=event_type,
                    )
                    .first()
                )
                if pref and not pref.enabled:
                    logger.info(
                        "dispatch_sync_opted_out",
                        user_id=user_id,
                        channel=channel_str,
                        event_type=event_type,
                    )
                    continue

                # Quiet hours check (UTC hour)
                if pref and pref.quiet_hours_start is not None and pref.quiet_hours_end is not None:
                    hour = datetime.now(UTC).hour
                    qs, qe = pref.quiet_hours_start, pref.quiet_hours_end
                    in_quiet = (qs <= qe and qs <= hour < qe) or (
                        qs > qe and (hour >= qs or hour < qe)
                    )
                    if in_quiet:
                        logger.info(
                            "dispatch_sync_quiet_hours",
                            user_id=user_id,
                            channel=channel_str,
                        )
                        continue

                # Create Notification record
                notif = Notification(
                    user_id=user.id,
                    channel=channel,
                    event_type=event_type,
                    priority=NotificationPriority(priority),
                    title=title,
                    message=message,
                    data={**extra, "title": title, "message": message},
                    status=NotificationStatus.PENDING,
                    tenant_id=tenant_id or user.tenant_id,
                )
                db.add(notif)
                db.flush()
                notification_id = str(notif.id)

                task_extra = {**extra, "title": title, "message": message}

                # Queue delivery task
                if channel == NotificationChannel.EMAIL:
                    send_email_notification_task.delay(
                        notification_id=notification_id,
                        to_email=user.email,
                        event_type=event_type,
                        user_name=user.name or user.email,
                        extra=task_extra,
                    )
                elif channel == NotificationChannel.WHATSAPP:
                    send_whatsapp_notification_task.delay(
                        notification_id=notification_id,
                        to_number=user.whatsapp_number,
                        event_type=event_type,
                        user_name=user.name or user.email,
                        extra=task_extra,
                    )
                elif channel == NotificationChannel.IN_APP:
                    send_inapp_notification_task.delay(
                        notification_id=notification_id,
                        user_id=user_id,
                    )

                logger.info(
                    "dispatch_sync_queued",
                    notification_id=notification_id,
                    channel=channel_str,
                    event_type=event_type,
                    user_id=user_id,
                )

    except Exception as exc:
        logger.error(
            "dispatch_sync_error",
            user_id=user_id,
            event_type=event_type,
            error=str(exc),
        )


# ── Async dispatcher (FastAPI routes) ─────────────────────────────────────────


async def dispatch_async(
    db: Any,
    user: Any,
    channels: list[str],
    event_type: str,
    title: str,
    message: str,
    priority: str = NotificationPriority.MEDIUM,
    extra: dict[str, Any] | None = None,
) -> None:
    """
    Create Notification records and queue delivery tasks from an async FastAPI route.

    Args:
        db:         AsyncSession from FastAPI dependency.
        user:       The User ORM object (already loaded).
        channels:   List of channel strings: "email", "in_app", "whatsapp".
        event_type: Canonical event type.
        title:      Short notification title.
        message:    Notification body text.
        priority:   One of NotificationPriority values.
        extra:      Additional payload forwarded to the delivery task.
    """
    from sqlalchemy import and_
    from sqlalchemy.future import select

    from app.models.notification import NotificationPreference
    from app.workers.notification_tasks import (
        send_email_notification_task,
        send_inapp_notification_task,
        send_whatsapp_notification_task,
    )

    extra = extra or {}

    try:
        for channel_str in channels:
            try:
                channel = NotificationChannel(channel_str)
            except ValueError:
                continue

            if channel == NotificationChannel.EMAIL and not user.email:
                continue
            if channel == NotificationChannel.WHATSAPP and not user.whatsapp_number:
                continue

            # Check preference opt-out
            pref_result = await db.execute(
                select(NotificationPreference).where(
                    and_(
                        NotificationPreference.user_id == user.id,
                        NotificationPreference.channel == channel,
                        NotificationPreference.event_type == event_type,
                    )
                )
            )
            pref = pref_result.scalar_one_or_none()
            if pref and not pref.enabled:
                continue

            # Quiet hours check
            if pref and pref.quiet_hours_start is not None and pref.quiet_hours_end is not None:
                hour = datetime.now(UTC).hour
                qs, qe = pref.quiet_hours_start, pref.quiet_hours_end
                in_quiet = (qs <= qe and qs <= hour < qe) or (qs > qe and (hour >= qs or hour < qe))
                if in_quiet:
                    continue

            # Create Notification record
            notif = Notification(
                user_id=user.id,
                channel=channel,
                event_type=event_type,
                priority=NotificationPriority(priority),
                title=title,
                message=message,
                data={**extra, "title": title, "message": message},
                status=NotificationStatus.PENDING,
                tenant_id=user.tenant_id,
            )
            db.add(notif)
            await db.flush()
            notification_id = str(notif.id)
            user_id = str(user.id)

            task_extra = {**extra, "title": title, "message": message}

            if channel == NotificationChannel.EMAIL:
                send_email_notification_task.delay(
                    notification_id=notification_id,
                    to_email=user.email,
                    event_type=event_type,
                    user_name=user.name or user.email,
                    extra=task_extra,
                )
            elif channel == NotificationChannel.WHATSAPP:
                send_whatsapp_notification_task.delay(
                    notification_id=notification_id,
                    to_number=user.whatsapp_number,
                    event_type=event_type,
                    user_name=user.name or user.email,
                    extra=task_extra,
                )
            elif channel == NotificationChannel.IN_APP:
                send_inapp_notification_task.delay(
                    notification_id=notification_id,
                    user_id=user_id,
                )

            logger.info(
                "dispatch_async_queued",
                notification_id=notification_id,
                channel=channel_str,
                event_type=event_type,
                user_id=user_id,
            )

    except Exception as exc:
        logger.error(
            "dispatch_async_error",
            user_id=str(user.id),
            event_type=event_type,
            error=str(exc),
        )
