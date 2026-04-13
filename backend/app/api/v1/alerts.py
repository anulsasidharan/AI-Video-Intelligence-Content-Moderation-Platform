"""
Alerts API — real-time moderation alerts from live streams.

GET   /alerts           list recent undismissed alerts for the current user
PATCH /alerts/{id}/dismiss   dismiss a single alert
POST  /alerts/dismiss-all    dismiss all alerts for the current user
"""

import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, OperatorUser
from app.core.exceptions import NotFoundError
from app.dependencies import get_db
from app.models.alert import Alert, AlertSeverity, LiveStream
from app.schemas.alerts import AlertListResponse, AlertResponse

router = APIRouter(prefix="/alerts", tags=["alerts"])
logger = structlog.get_logger(__name__)


@router.post(
    "",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a live stream alert and notify the stream owner",
)
async def create_alert(
    stream_id: uuid.UUID,
    severity: AlertSeverity,
    message: str,
    current_user: OperatorUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    category: str | None = None,
    frame_url: str | None = None,
) -> AlertResponse:
    """
    Persist a live stream moderation alert and fire in-app + WhatsApp notifications
    to the stream owner.
    """
    alert = Alert(
        stream_id=stream_id,
        severity=severity,
        message=message,
        category=category,
        frame_url=frame_url,
        tenant_id=current_user.tenant_id if current_user else None,
    )
    db.add(alert)
    await db.flush()
    logger.info("alert_created", alert_id=str(alert.id), stream_id=str(stream_id))

    # Look up stream owner and notify
    stream_result = await db.execute(select(LiveStream).where(LiveStream.id == stream_id))
    stream = stream_result.scalar_one_or_none()
    if stream:
        from app.models.user import User

        owner = await db.get(User, stream.owner_id)
        if owner:
            from app.services.notification_dispatcher import dispatch_async

            notif_channels = ["in_app"]
            if severity in (AlertSeverity.HIGH, AlertSeverity.CRITICAL) and owner.whatsapp_number:
                notif_channels.append("whatsapp")
            if severity == AlertSeverity.CRITICAL:
                notif_channels.append("email")
            await dispatch_async(
                db=db,
                user=owner,
                channels=notif_channels,
                event_type="stream.alert",
                title=f"Live stream alert — {severity.value.upper()}",
                message=message,
                priority=severity.value,
                extra={
                    "stream_title": stream.title,
                    "stream_id": str(stream_id),
                    "category": category or "unknown",
                    "severity": severity.value,
                    "confidence": 1.0,
                },
            )

    return AlertResponse.model_validate(alert)


@router.get(
    "",
    response_model=AlertListResponse,
    summary="List recent alerts for the current user",
)
async def list_alerts(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    dismissed: bool = Query(False, description="Include dismissed alerts"),
    limit: int = Query(50, ge=1, le=200),
) -> AlertListResponse:
    q = select(Alert)
    if current_user.tenant_id:
        q = q.where(Alert.tenant_id == current_user.tenant_id)
    if not dismissed:
        q = q.where(Alert.is_dismissed.is_(False))
    q = q.order_by(Alert.created_at.desc()).limit(limit)

    result = await db.execute(q)
    alerts = result.scalars().all()
    return AlertListResponse(
        items=[AlertResponse.model_validate(a) for a in alerts],
        total=len(alerts),
    )


@router.patch(
    "/{alert_id}/dismiss",
    response_model=AlertResponse,
    summary="Dismiss a single alert",
)
async def dismiss_alert(
    alert_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AlertResponse:
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise NotFoundError("Alert", str(alert_id))

    alert.is_dismissed = True
    await db.flush()
    logger.info("alert_dismissed", alert_id=str(alert_id), user_id=str(current_user.id))
    return AlertResponse.model_validate(alert)


@router.post(
    "/dismiss-all",
    summary="Dismiss all undismissed alerts for the current user",
)
async def dismiss_all_alerts(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    q = update(Alert).where(Alert.is_dismissed.is_(False))
    if current_user.tenant_id:
        q = q.where(Alert.tenant_id == current_user.tenant_id)
    q = q.values(is_dismissed=True)

    result = await db.execute(q)
    logger.info("all_alerts_dismissed", user_id=str(current_user.id), count=result.rowcount)
    return {"dismissed": result.rowcount}
