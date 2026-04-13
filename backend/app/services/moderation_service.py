"""
S-03 ModerationService

Decision engine for moderation queue management, human review submission,
admin override, and re-moderation dispatch.

Public API:
    await service.list_queue(tenant_id, page, page_size, status_filter) -> PaginatedQueue
    await service.get_result(video_id)                                   -> ModerationResultResponse
    await service.submit_review(moderation_id, reviewer_id, body)       -> ModerationResultResponse
    await service.override_decision(moderation_id, admin_id, body)      -> ModerationResultResponse
    await service.trigger_remoderation(video_id, policy_rules)          -> dict
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import NotFoundError
from app.models.moderation import (
    ModerationQueueItem,
    ModerationResult,
    ModerationStatus,
    ReviewAction,
)
from app.schemas.moderation import (
    ModerationQueueItemResponse,
    ModerationResultResponse,
    OverrideRequest,
    PaginatedQueue,
    SubmitReviewRequest,
)

logger = structlog.get_logger(__name__)

_REVIEW_ACTION_TO_STATUS: dict[ReviewAction, ModerationStatus] = {
    ReviewAction.APPROVE: ModerationStatus.APPROVED,
    ReviewAction.REJECT: ModerationStatus.REJECTED,
    ReviewAction.ESCALATE: ModerationStatus.ESCALATED,
}


class ModerationService:
    """Handles queue management, review decisions, and remoderation dispatch."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Queue ──────────────────────────────────────────────────────────────────

    async def list_queue(
        self,
        tenant_id: str | None = None,
        page: int = 1,
        page_size: int = settings.DEFAULT_PAGE_SIZE,
        status_filter: ModerationStatus | None = None,
    ) -> PaginatedQueue:
        """
        Return a paginated moderation queue, optionally scoped by tenant and status.

        Args:
            tenant_id:     Tenant scope; None returns all tenants (admin use).
            page:          1-based page number.
            page_size:     Items per page.
            status_filter: Optional status enum to filter by.

        Returns:
            PaginatedQueue schema.
        """
        base_query = select(ModerationQueueItem)
        if tenant_id:
            base_query = base_query.where(ModerationQueueItem.tenant_id == tenant_id)
        if status_filter:
            base_query = base_query.where(ModerationQueueItem.status == status_filter)

        count_result = await self._db.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total = count_result.scalar_one()

        result = await self._db.execute(
            base_query.order_by(
                ModerationQueueItem.priority.desc(),
                ModerationQueueItem.created_at.asc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = result.scalars().all()

        return PaginatedQueue(
            items=[
                ModerationQueueItemResponse(
                    id=item.id,
                    video_id=item.video_id,
                    moderation_result_id=item.moderation_result_id,
                    status=item.status,
                    priority=item.priority,
                    assigned_to=item.assigned_to,
                    tenant_id=item.tenant_id,
                    created_at=item.created_at,
                )
                for item in items
            ],
            total=total,
            page=page,
            page_size=page_size,
        )

    # ── Result ─────────────────────────────────────────────────────────────────

    async def get_result(self, video_id: uuid.UUID) -> ModerationResultResponse:
        """
        Return the full AI moderation result for a given video.

        Raises:
            NotFoundError: If no result exists for the video.
        """
        result = await self._db.execute(
            select(ModerationResult).where(ModerationResult.video_id == video_id)
        )
        moderation = result.scalar_one_or_none()
        if not moderation:
            raise NotFoundError("ModerationResult", str(video_id))

        return ModerationResultResponse.model_validate(moderation)

    # ── Human review ───────────────────────────────────────────────────────────

    async def submit_review(
        self,
        moderation_id: uuid.UUID,
        reviewer_id: uuid.UUID,
        body: SubmitReviewRequest,
    ) -> ModerationResultResponse:
        """
        Record a human reviewer's decision (approve / reject / escalate).

        Updates the ModerationResult and its linked ModerationQueueItem.

        Raises:
            NotFoundError: If the ModerationResult doesn't exist.

        Returns:
            Updated ModerationResultResponse.
        """
        result = await self._db.execute(
            select(ModerationResult).where(ModerationResult.id == moderation_id)
        )
        moderation = result.scalar_one_or_none()
        if not moderation:
            raise NotFoundError("ModerationResult", str(moderation_id))

        new_status = _REVIEW_ACTION_TO_STATUS[body.action]
        moderation.status = new_status
        moderation.reviewed_by = reviewer_id
        moderation.review_action = body.action
        moderation.review_notes = body.notes
        moderation.reviewed_at = datetime.now(UTC).isoformat()

        # Mirror status on the linked queue item
        queue_result = await self._db.execute(
            select(ModerationQueueItem).where(
                ModerationQueueItem.moderation_result_id == moderation_id
            )
        )
        queue_item = queue_result.scalar_one_or_none()
        if queue_item:
            queue_item.status = new_status

        logger.info(
            "review_submitted",
            moderation_id=str(moderation_id),
            action=body.action.value,
            reviewer_id=str(reviewer_id),
        )
        return ModerationResultResponse.model_validate(moderation)

    # ── Admin override ─────────────────────────────────────────────────────────

    async def override_decision(
        self,
        moderation_id: uuid.UUID,
        admin_id: uuid.UUID,
        body: OverrideRequest,
    ) -> ModerationResultResponse:
        """
        Admin override of an AI or human moderation decision.

        Raises:
            NotFoundError: If the ModerationResult doesn't exist.

        Returns:
            Updated ModerationResultResponse.
        """
        result = await self._db.execute(
            select(ModerationResult).where(ModerationResult.id == moderation_id)
        )
        moderation = result.scalar_one_or_none()
        if not moderation:
            raise NotFoundError("ModerationResult", str(moderation_id))

        moderation.override_by = admin_id
        moderation.override_decision = body.decision
        moderation.override_at = datetime.now(UTC).isoformat()

        logger.info(
            "decision_overridden",
            moderation_id=str(moderation_id),
            decision=body.decision,
            admin_id=str(admin_id),
        )
        return ModerationResultResponse.model_validate(moderation)

    # ── Re-moderation ──────────────────────────────────────────────────────────

    async def trigger_remoderation(
        self,
        video_id: uuid.UUID,
        policy_rules: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Enqueue a re-moderation run for an already-processed video.

        Looks up the existing ModerationResult to pass current violations and
        summary to the workflow.

        Args:
            video_id:     UUID of the video to re-moderate.
            policy_rules: Active policy rule dicts to apply.

        Returns:
            Celery async result ID dict: {"task_id": str, "video_id": str}.
        """
        result = await self._db.execute(
            select(ModerationResult).where(ModerationResult.video_id == video_id)
        )
        moderation = result.scalar_one_or_none()

        content_summary = moderation.summary or "" if moderation else ""
        violations = moderation.violations or [] if moderation else []

        from app.workers.moderation_tasks import run_moderation_task

        task = run_moderation_task.delay(
            video_id=str(video_id),
            policy_rules=policy_rules or [],
            content_summary=content_summary,
            violations=violations,
        )

        logger.info("remoderation_triggered", video_id=str(video_id), task_id=task.id)
        return {"task_id": task.id, "video_id": str(video_id)}
