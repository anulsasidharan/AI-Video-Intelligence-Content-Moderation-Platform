"""Tests for S-03 ModerationService — DB mocked."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import NotFoundError
from app.models.moderation import ModerationStatus, ReviewAction

# ── Helpers ────────────────────────────────────────────────────────────────────

_MOD_ID = uuid.uuid4()
_VIDEO_ID = uuid.uuid4()
_REVIEWER_ID = uuid.uuid4()
_ADMIN_ID = uuid.uuid4()


def _make_moderation(mod_id=None, video_id=None):
    m = MagicMock()
    m.id = mod_id or _MOD_ID
    m.video_id = video_id or _VIDEO_ID
    m.status = ModerationStatus.PENDING
    m.summary = "Test summary."
    m.violations = []
    m.reviewed_by = None
    m.review_action = None
    m.review_notes = None
    m.reviewed_at = None
    m.override_by = None
    m.override_decision = None
    m.override_at = None
    return m


def _make_queue_item():
    item = MagicMock()
    item.id = uuid.uuid4()
    item.video_id = _VIDEO_ID
    item.moderation_result_id = _MOD_ID
    item.status = ModerationStatus.PENDING
    item.priority = 0
    item.assigned_to = None
    item.tenant_id = None
    item.created_at = None
    return item


def _make_db(moderation=None, queue_item=None, total=0):
    """Return a mock AsyncSession."""
    db = AsyncMock()

    def _execute_side_effect(*args, **kwargs):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = moderation
        mock_result.scalar_one.return_value = total
        mock_result.scalars.return_value.all.return_value = []
        return mock_result

    db.execute = AsyncMock(side_effect=_execute_side_effect)
    db.scalar = AsyncMock(return_value=total)
    return db


# ── get_result ─────────────────────────────────────────────────────────────────


class TestGetResult:
    @pytest.mark.asyncio
    async def test_returns_result_when_found(self):
        from app.services.moderation_service import ModerationService

        moderation = _make_moderation()
        db = _make_db(moderation=moderation)

        with patch("app.services.moderation_service.ModerationResultResponse") as MockResp:
            MockResp.model_validate.return_value = MagicMock(id=moderation.id)
            service = ModerationService(db=db)
            await service.get_result(_VIDEO_ID)

        MockResp.model_validate.assert_called_once_with(moderation)

    @pytest.mark.asyncio
    async def test_raises_not_found_when_missing(self):
        from app.services.moderation_service import ModerationService

        db = _make_db(moderation=None)
        service = ModerationService(db=db)
        with pytest.raises(NotFoundError):
            await service.get_result(uuid.uuid4())


# ── submit_review ──────────────────────────────────────────────────────────────


class TestSubmitReview:
    @pytest.mark.asyncio
    async def test_updates_status_and_reviewer(self):
        from app.schemas.moderation import SubmitReviewRequest
        from app.services.moderation_service import ModerationService

        moderation = _make_moderation()
        db = _make_db(moderation=moderation)

        body = MagicMock(spec=SubmitReviewRequest)
        body.action = ReviewAction.APPROVE
        body.notes = "Looks fine."

        with patch("app.services.moderation_service.ModerationResultResponse") as MockResp:
            MockResp.model_validate.return_value = MagicMock()
            service = ModerationService(db=db)
            await service.submit_review(_MOD_ID, _REVIEWER_ID, body)

        assert moderation.status == ModerationStatus.APPROVED
        assert moderation.reviewed_by == _REVIEWER_ID
        assert moderation.review_action == ReviewAction.APPROVE
        assert moderation.review_notes == "Looks fine."

    @pytest.mark.asyncio
    async def test_raises_not_found_on_missing_moderation(self):
        from app.schemas.moderation import SubmitReviewRequest
        from app.services.moderation_service import ModerationService

        db = _make_db(moderation=None)
        body = MagicMock(spec=SubmitReviewRequest)
        body.action = ReviewAction.REJECT

        service = ModerationService(db=db)
        with pytest.raises(NotFoundError):
            await service.submit_review(uuid.uuid4(), _REVIEWER_ID, body)


# ── override_decision ──────────────────────────────────────────────────────────


class TestOverrideDecision:
    @pytest.mark.asyncio
    async def test_sets_override_fields(self):
        from app.schemas.moderation import OverrideRequest
        from app.services.moderation_service import ModerationService

        moderation = _make_moderation()
        db = _make_db(moderation=moderation)

        body = MagicMock(spec=OverrideRequest)
        body.decision = "approved"

        with patch("app.services.moderation_service.ModerationResultResponse") as MockResp:
            MockResp.model_validate.return_value = MagicMock()
            service = ModerationService(db=db)
            await service.override_decision(_MOD_ID, _ADMIN_ID, body)

        assert moderation.override_by == _ADMIN_ID
        assert moderation.override_decision == "approved"
        assert moderation.override_at is not None

    @pytest.mark.asyncio
    async def test_raises_not_found_on_missing_moderation(self):
        from app.schemas.moderation import OverrideRequest
        from app.services.moderation_service import ModerationService

        db = _make_db(moderation=None)
        body = MagicMock(spec=OverrideRequest)
        body.decision = "rejected"

        service = ModerationService(db=db)
        with pytest.raises(NotFoundError):
            await service.override_decision(uuid.uuid4(), _ADMIN_ID, body)


# ── trigger_remoderation ───────────────────────────────────────────────────────


class TestTriggerRemoderation:
    @pytest.mark.asyncio
    async def test_enqueues_task_and_returns_task_id(self):
        from app.services.moderation_service import ModerationService

        moderation = _make_moderation()
        db = _make_db(moderation=moderation)

        mock_task = MagicMock()
        mock_task.id = "celery-task-id-123"

        with patch("app.workers.moderation_tasks.run_moderation_task") as mock_run:
            mock_run.delay.return_value = mock_task
            service = ModerationService(db=db)
            result = await service.trigger_remoderation(_VIDEO_ID)

        mock_run.delay.assert_called_once()
        assert result["task_id"] == "celery-task-id-123"
        assert result["video_id"] == str(_VIDEO_ID)
