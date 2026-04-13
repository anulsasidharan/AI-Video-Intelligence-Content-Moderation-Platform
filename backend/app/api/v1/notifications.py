"""
Notifications API — N-01

Endpoints for in-app notification management and user preference configuration.

Routes:
    GET    /notifications                   — list user's in-app notifications
    PATCH  /notifications/{id}/read         — mark single notification as read
    POST   /notifications/read-all          — mark all in-app as read
    DELETE /notifications/{id}              — delete a notification
    GET    /notifications/preferences       — get user's channel preferences
    PUT    /notifications/preferences       — upsert user's channel preferences
    POST   /notifications/send              — admin: dispatch ad-hoc notification
    GET    /notifications/event-types       — list supported event types
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, OperatorUser
from app.core.exceptions import NotFoundError
from app.dependencies import get_db
from app.models.notification import (
    NOTIFICATION_EVENT_TYPES,
    Notification,
    NotificationChannel,
    NotificationPreference,
    NotificationStatus,
)
from app.models.user import User
from app.schemas.notification import (
    NotificationListResponse,
    NotificationPreferenceItem,
    NotificationPreferencesRequest,
    NotificationPreferencesResponse,
    NotificationResponse,
    NotificationSendRequest,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])
logger = structlog.get_logger(__name__)


# ── GET /notifications ─────────────────────────────────────────────────────────


@router.get(
    "",
    response_model=NotificationListResponse,
    summary="List in-app notifications for the current user",
)
async def list_notifications(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 50,
    offset: int = 0,
    unread_only: bool = False,
) -> NotificationListResponse:
    filters = [
        Notification.user_id == current_user.id,
        Notification.channel == NotificationChannel.IN_APP,
    ]
    if unread_only:
        filters.append(Notification.status != NotificationStatus.READ)

    q = select(Notification).where(and_(*filters))
    total = await db.scalar(select(func.count()).select_from(q.subquery())) or 0

    result = await db.execute(
        q.order_by(Notification.created_at.desc()).limit(limit).offset(offset)
    )
    items = result.scalars().all()

    unread_q = select(func.count(Notification.id)).where(
        and_(
            Notification.user_id == current_user.id,
            Notification.channel == NotificationChannel.IN_APP,
            Notification.status != NotificationStatus.READ,
        )
    )
    unread_count = await db.scalar(unread_q) or 0

    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in items],
        total=total,
        unread_count=unread_count,
    )


# ── PATCH /notifications/{id}/read ────────────────────────────────────────────


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    summary="Mark a notification as read",
)
async def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> NotificationResponse:
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notif = result.scalar_one_or_none()
    if not notif:
        raise NotFoundError("Notification", str(notification_id))

    notif.status = NotificationStatus.READ
    notif.read_at = datetime.now(UTC)

    logger.info("notification_marked_read", notification_id=str(notification_id))
    return NotificationResponse.model_validate(notif)


# ── POST /notifications/read-all ──────────────────────────────────────────────


@router.post(
    "/read-all",
    status_code=status.HTTP_200_OK,
    summary="Mark all in-app notifications as read",
)
async def mark_all_read(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    result = await db.execute(
        select(Notification).where(
            Notification.user_id == current_user.id,
            Notification.channel == NotificationChannel.IN_APP,
            Notification.status != NotificationStatus.READ,
        )
    )
    notifications = result.scalars().all()
    now = datetime.now(UTC)
    for notif in notifications:
        notif.status = NotificationStatus.READ
        notif.read_at = now

    logger.info(
        "all_notifications_marked_read",
        user_id=str(current_user.id),
        count=len(notifications),
    )
    return {"marked_read": len(notifications)}


# ── DELETE /notifications/{id} ────────────────────────────────────────────────


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Delete a notification",
)
async def delete_notification(
    notification_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notif = result.scalar_one_or_none()
    if not notif:
        raise NotFoundError("Notification", str(notification_id))

    await db.delete(notif)
    logger.info("notification_deleted", notification_id=str(notification_id))


# ── GET /notifications/preferences ────────────────────────────────────────────


@router.get(
    "/preferences",
    response_model=NotificationPreferencesResponse,
    summary="Get notification preferences for the current user",
)
async def get_preferences(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> NotificationPreferencesResponse:
    result = await db.execute(
        select(NotificationPreference)
        .where(NotificationPreference.user_id == current_user.id)
        .order_by(NotificationPreference.channel, NotificationPreference.event_type)
    )
    prefs = result.scalars().all()
    return NotificationPreferencesResponse(
        items=[NotificationPreferenceItem.model_validate(p) for p in prefs],
        total=len(prefs),
    )


# ── PUT /notifications/preferences ────────────────────────────────────────────


@router.put(
    "/preferences",
    response_model=NotificationPreferencesResponse,
    summary="Upsert notification preferences",
)
async def update_preferences(
    body: NotificationPreferencesRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> NotificationPreferencesResponse:
    upserted: list[NotificationPreference] = []

    for pref_in in body.preferences:
        result = await db.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id == current_user.id,
                NotificationPreference.channel == pref_in.channel,
                NotificationPreference.event_type == pref_in.event_type,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.enabled = pref_in.enabled
            existing.quiet_hours_start = pref_in.quiet_hours_start
            existing.quiet_hours_end = pref_in.quiet_hours_end
            existing.frequency = pref_in.frequency
            upserted.append(existing)
        else:
            new_pref = NotificationPreference(
                user_id=current_user.id,
                channel=pref_in.channel,
                event_type=pref_in.event_type,
                enabled=pref_in.enabled,
                quiet_hours_start=pref_in.quiet_hours_start,
                quiet_hours_end=pref_in.quiet_hours_end,
                frequency=pref_in.frequency,
                tenant_id=current_user.tenant_id,
            )
            db.add(new_pref)
            await db.flush()
            upserted.append(new_pref)

    logger.info(
        "notification_preferences_updated",
        user_id=str(current_user.id),
        count=len(upserted),
    )
    return NotificationPreferencesResponse(
        items=[NotificationPreferenceItem.model_validate(p) for p in upserted],
        total=len(upserted),
    )


# ── POST /notifications/send ──────────────────────────────────────────────────


@router.post(
    "/send",
    status_code=status.HTTP_202_ACCEPTED,
    summary="[Admin] Dispatch an ad-hoc notification to a user",
)
async def send_notification(
    body: NotificationSendRequest,
    current_user: OperatorUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """
    Create a Notification record and enqueue the appropriate Celery delivery task.

    The task chosen depends on body.channel:
      - in_app   → send_inapp_notification_task
      - email    → send_email_notification_task
      - whatsapp → send_whatsapp_notification_task

    Respects user preferences: if the target user has disabled the channel/event_type
    combination, the notification is still created but logged as skipped.
    """
    from app.workers.notification_tasks import (
        send_email_notification_task,
        send_inapp_notification_task,
        send_whatsapp_notification_task,
    )

    # Check recipient exists
    recipient = await db.get(User, body.user_id)
    if not recipient:
        raise NotFoundError("User", str(body.user_id))

    # Check preference (skip if user opted out)
    pref_result = await db.execute(
        select(NotificationPreference).where(
            NotificationPreference.user_id == body.user_id,
            NotificationPreference.channel == body.channel,
            NotificationPreference.event_type == body.event_type,
        )
    )
    pref = pref_result.scalar_one_or_none()
    if pref and not pref.enabled:
        logger.info(
            "notification_skipped_user_opted_out",
            user_id=str(body.user_id),
            channel=body.channel,
            event_type=body.event_type,
        )
        return {"queued": False, "reason": "user_opted_out"}

    # Quiet hours check (hour-of-day in UTC)
    if pref and pref.quiet_hours_start is not None and pref.quiet_hours_end is not None:
        current_hour = datetime.now(UTC).hour
        qs, qe = pref.quiet_hours_start, pref.quiet_hours_end
        in_quiet = (qs <= qe and qs <= current_hour < qe) or (
            qs > qe and (current_hour >= qs or current_hour < qe)
        )
        if in_quiet:
            logger.info(
                "notification_deferred_quiet_hours",
                user_id=str(body.user_id),
                channel=body.channel,
            )
            return {"queued": False, "reason": "quiet_hours"}

    # Persist the notification record
    notif = Notification(
        user_id=body.user_id,
        channel=body.channel,
        event_type=body.event_type,
        priority=body.priority,
        title=body.title,
        message=body.message,
        data=body.data,
        scheduled_at=body.scheduled_at,
        tenant_id=recipient.tenant_id,
    )
    db.add(notif)
    await db.flush()
    notification_id = str(notif.id)

    extra = {
        **(body.data or {}),
        "title": body.title,
        "message": body.message,
    }

    # Dispatch Celery task by channel
    if body.channel == NotificationChannel.IN_APP:
        send_inapp_notification_task.delay(
            notification_id=notification_id,
            user_id=str(body.user_id),
        )
    elif body.channel == NotificationChannel.EMAIL:
        if not recipient.email:
            return {"queued": False, "reason": "no_email_on_record"}
        send_email_notification_task.delay(
            notification_id=notification_id,
            to_email=recipient.email,
            event_type=body.event_type,
            user_name=recipient.name or recipient.email,
            extra=extra,
        )
    elif body.channel == NotificationChannel.WHATSAPP:
        if not recipient.whatsapp_number:
            return {"queued": False, "reason": "no_whatsapp_number_on_record"}
        send_whatsapp_notification_task.delay(
            notification_id=notification_id,
            to_number=recipient.whatsapp_number,
            event_type=body.event_type,
            user_name=recipient.name or recipient.email,
            extra=extra,
        )

    logger.info(
        "notification_queued",
        notification_id=notification_id,
        channel=body.channel,
        event_type=body.event_type,
        user_id=str(body.user_id),
    )
    return {"queued": True, "notification_id": notification_id}


# ── GET /notifications/event-types ────────────────────────────────────────────


@router.get(
    "/event-types",
    summary="List supported notification event types",
)
async def list_event_types() -> dict:
    return {"event_types": NOTIFICATION_EVENT_TYPES}


# ── POST /notifications/test ──────────────────────────────────────────────────


@router.post(
    "/test",
    summary="Send a test notification to yourself (email or whatsapp)",
)
async def test_notification(
    channel: str,
    current_user: CurrentUser,
) -> dict:
    """
    Fire a test notification synchronously to the calling user.

    Runs the delivery task in-process (no Celery queue) and returns the result
    or the exact error — useful for verifying SendGrid / Twilio credentials and
    sender configuration without needing to upload a video.

    Query params:
        channel: "email" | "whatsapp"

    Requirements:
        - email:    user must have an email address (always true after registration)
        - whatsapp: user must have whatsapp_number set in their profile (E.164)
    """
    from app.services.email_service import EmailService
    from app.services.whatsapp_service import WhatsAppService

    if channel == "email":
        if not current_user.email:
            return {"sent": False, "error": "No email address on your account"}
        try:
            svc = EmailService()
            result = svc.send_moderation_complete(
                to_email=current_user.email,
                user_name=current_user.name or current_user.email,
                video_title="Test Video — notification check",
                status="approved",
                report_url=None,
            )
            logger.info("test_email_sent", user_id=str(current_user.id), **result)
            return {"sent": True, "channel": "email", "to": current_user.email, **result}
        except Exception as exc:
            logger.error("test_email_failed", user_id=str(current_user.id), error=str(exc))
            return {"sent": False, "channel": "email", "error": str(exc)}

    elif channel == "whatsapp":
        if not current_user.whatsapp_number:
            return {
                "sent": False,
                "error": "No WhatsApp number on your account. "
                "Add it in Dashboard → Profile (E.164 format, e.g. +919876543210).",
            }
        try:
            svc = WhatsAppService()
            result = svc.send_moderation_complete(
                to_number=current_user.whatsapp_number,
                user_name=current_user.name or current_user.email,
                video_title="Test Video — notification check",
                status="approved",
            )
            logger.info("test_whatsapp_sent", user_id=str(current_user.id), **result)
            return {
                "sent": True,
                "channel": "whatsapp",
                "to": current_user.whatsapp_number,
                **result,
            }
        except Exception as exc:
            logger.error("test_whatsapp_failed", user_id=str(current_user.id), error=str(exc))
            return {"sent": False, "channel": "whatsapp", "error": str(exc)}

    return {"sent": False, "error": f"Unknown channel '{channel}'. Use 'email' or 'whatsapp'."}
