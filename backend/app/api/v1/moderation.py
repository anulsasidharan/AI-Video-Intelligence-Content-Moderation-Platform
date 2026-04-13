"""
Moderation API — B-03
Queue management, AI result retrieval, human review, and admin override.
"""

import uuid
from datetime import UTC, datetime
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import delete as sql_delete
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AdminUser, CurrentUser, OperatorUser
from app.config import settings
from app.core.exceptions import NotFoundError
from app.dependencies import get_db
from app.models.moderation import (
    ModerationQueueItem,
    ModerationResult,
    ModerationStatus,
    ReviewAction,
)
from app.models.user import UserRole
from app.models.video import Video
from app.schemas.moderation import (
    ClearQueueResponse,
    ModerationQueueItemResponse,
    ModerationResultResponse,
    OverrideRequest,
    PaginatedQueue,
    SubmitReviewRequest,
)

router = APIRouter(prefix="/moderation", tags=["moderation"])
logger = structlog.get_logger(__name__)


# ── GET /moderation/queue ─────────────────────────────────────────────────────


@router.get(
    "/queue",
    response_model=PaginatedQueue,
    summary="List moderation queue with status and category filters",
)
async def list_queue(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    status_filter: ModerationStatus | None = Query(None, alias="status"),  # noqa: B008
) -> PaginatedQueue:
    base_query = select(ModerationQueueItem)
    if current_user.tenant_id:
        base_query = base_query.where(ModerationQueueItem.tenant_id == current_user.tenant_id)
    if status_filter:
        base_query = base_query.where(ModerationQueueItem.status == status_filter)
    # Admins and operators see all items; regular users only see their own videos' items
    if current_user.role not in (UserRole.ADMIN, UserRole.OPERATOR):
        base_query = base_query.where(
            ModerationQueueItem.video_id.in_(
                select(Video.id).where(Video.owner_id == current_user.id)
            )
        )

    count_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total = count_result.scalar_one()

    result = await db.execute(
        base_query.order_by(
            ModerationQueueItem.priority.desc(), ModerationQueueItem.created_at.asc()
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = result.scalars().all()

    # Batch-load related ModerationResult rows
    result_ids = [i.moderation_result_id for i in items if i.moderation_result_id]
    video_ids = [i.video_id for i in items]

    mod_results: dict = {}
    if result_ids:
        mr = await db.execute(select(ModerationResult).where(ModerationResult.id.in_(result_ids)))
        mod_results = {r.id: r for r in mr.scalars().all()}

    video_titles: dict = {}
    if video_ids:
        vr = await db.execute(select(Video).where(Video.id.in_(video_ids)))
        video_titles = {v.id: v.title for v in vr.scalars().all()}

    response_items = []
    for item in items:
        mr = mod_results.get(item.moderation_result_id) if item.moderation_result_id else None
        response_items.append(
            ModerationQueueItemResponse(
                id=item.id,
                video_id=item.video_id,
                moderation_result_id=item.moderation_result_id,
                status=item.status,
                priority=item.priority,
                assigned_to=item.assigned_to,
                tenant_id=item.tenant_id,
                created_at=item.created_at,
                video_title=video_titles.get(item.video_id),
                # Justification fields from ModerationResult
                ai_summary=mr.summary if mr else None,
                overall_confidence=mr.overall_confidence if mr else None,
                violations=(mr.violations or []) if mr else [],
                ai_model=mr.ai_model if mr else None,
            )
        )

    return PaginatedQueue(
        items=response_items,
        total=total,
        page=page,
        page_size=page_size,
    )


# ── GET /moderation/videos/{video_id} ────────────────────────────────────────


@router.get(
    "/videos/{video_id}",
    response_model=ModerationResultResponse,
    summary="Get full AI moderation result for a video",
)
async def get_moderation_result(
    video_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ModerationResultResponse:
    result = await db.execute(select(ModerationResult).where(ModerationResult.video_id == video_id))
    moderation = result.scalar_one_or_none()
    if not moderation:
        raise NotFoundError("ModerationResult", str(video_id))

    return ModerationResultResponse.model_validate(moderation)


# ── POST /moderation/{moderation_id}/review ───────────────────────────────────


@router.post(
    "/{moderation_id}/review",
    response_model=ModerationResultResponse,
    summary="Submit a human review decision (approve / reject / escalate)",
)
async def submit_review(
    moderation_id: uuid.UUID,
    body: SubmitReviewRequest,
    current_user: OperatorUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ModerationResultResponse:
    # Try by ModerationResult.id first
    result = await db.execute(select(ModerationResult).where(ModerationResult.id == moderation_id))
    moderation = result.scalar_one_or_none()

    # Fallback: caller may have passed a queue item ID instead of a result ID
    queue_item = None
    if not moderation:
        qi_result = await db.execute(
            select(ModerationQueueItem).where(ModerationQueueItem.id == moderation_id)
        )
        queue_item = qi_result.scalar_one_or_none()
        if queue_item:
            if queue_item.moderation_result_id:
                # Follow the FK directly
                mr_result = await db.execute(
                    select(ModerationResult).where(
                        ModerationResult.id == queue_item.moderation_result_id
                    )
                )
                moderation = mr_result.scalar_one_or_none()
            if not moderation:
                # FK is null or stale — find by video_id and repair the link
                mr_result = await db.execute(
                    select(ModerationResult).where(ModerationResult.video_id == queue_item.video_id)
                )
                moderation = mr_result.scalar_one_or_none()
                if moderation:
                    queue_item.moderation_result_id = moderation.id

    if not moderation:
        raise NotFoundError("ModerationResult", str(moderation_id))

    status_map: dict[ReviewAction, ModerationStatus] = {
        ReviewAction.APPROVE: ModerationStatus.APPROVED,
        ReviewAction.REJECT: ModerationStatus.REJECTED,
        ReviewAction.ESCALATE: ModerationStatus.ESCALATED,
    }

    moderation.status = status_map[body.action]
    moderation.reviewed_by = current_user.id
    moderation.review_action = body.action
    moderation.review_notes = body.notes
    moderation.reviewed_at = datetime.now(UTC).isoformat()

    # Update queue item status — use the one we already found, or look it up by result ID
    if not queue_item:
        qi_result = await db.execute(
            select(ModerationQueueItem).where(
                ModerationQueueItem.moderation_result_id == moderation.id
            )
        )
        queue_item = qi_result.scalar_one_or_none()
    if queue_item:
        queue_item.status = status_map[body.action]

    logger.info(
        "review_submitted",
        moderation_id=str(moderation_id),
        action=body.action.value,
        reviewer=str(current_user.id),
    )
    # Stub: fire webhook event — notification_service.dispatch("moderation.reviewed", payload)
    return ModerationResultResponse.model_validate(moderation)


# ── PUT /moderation/{moderation_id}/override ─────────────────────────────────


@router.put(
    "/{moderation_id}/override",
    response_model=ModerationResultResponse,
    summary="Admin override of AI or human moderation decision",
)
async def override_decision(
    moderation_id: uuid.UUID,
    body: OverrideRequest,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ModerationResultResponse:
    result = await db.execute(select(ModerationResult).where(ModerationResult.id == moderation_id))
    moderation = result.scalar_one_or_none()
    if not moderation:
        raise NotFoundError("ModerationResult", str(moderation_id))

    moderation.override_by = current_user.id
    moderation.override_decision = body.decision
    moderation.override_at = datetime.now(UTC).isoformat()

    logger.info(
        "decision_overridden",
        moderation_id=str(moderation_id),
        decision=body.decision,
        admin=str(current_user.id),
    )
    return ModerationResultResponse.model_validate(moderation)


# ── DELETE /moderation/queue/clear ───────────────────────────────────────────


@router.delete(
    "/queue/clear",
    response_model=ClearQueueResponse,
    summary="Remove all decided (non-pending) queue items for the current user",
)
async def clear_finished_queue(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ClearQueueResponse:
    decided = [
        ModerationStatus.APPROVED,
        ModerationStatus.REJECTED,
        ModerationStatus.FLAGGED,
        ModerationStatus.ESCALATED,
    ]
    owned_video_ids = select(Video.id).where(Video.owner_id == current_user.id)

    result = await db.execute(
        sql_delete(ModerationQueueItem)
        .where(
            ModerationQueueItem.status.in_(decided),
            ModerationQueueItem.video_id.in_(owned_video_ids),
        )
        .returning(ModerationQueueItem.id)
    )
    removed = len(result.fetchall())
    await db.commit()

    logger.info("queue_cleared", user_id=str(current_user.id), removed=removed)
    return ClearQueueResponse(removed=removed)


# ── DELETE /moderation/queue/{item_id} ───────────────────────────────────────


@router.delete(
    "/queue/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Remove a single queue item",
)
async def delete_queue_item(
    item_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    owned_video_ids = select(Video.id).where(Video.owner_id == current_user.id)

    result = await db.execute(
        select(ModerationQueueItem).where(
            ModerationQueueItem.id == item_id,
            ModerationQueueItem.video_id.in_(owned_video_ids),
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundError("QueueItem", str(item_id))

    await db.delete(item)
    await db.commit()
    logger.info("queue_item_deleted", item_id=str(item_id), user_id=str(current_user.id))
