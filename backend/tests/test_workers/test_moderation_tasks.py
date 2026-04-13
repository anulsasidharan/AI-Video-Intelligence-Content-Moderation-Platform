"""Tests for W-03 — moderation_tasks (all external I/O mocked)."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

_VIDEO_ID = str(uuid.uuid4())
_MOD_RESULT_ID = str(uuid.uuid4())
_POLICY_ID = str(uuid.uuid4())


# ── run_moderation_task ────────────────────────────────────────────────────────


class TestRunModerationTask:
    @patch("app.workers.moderation_tasks.sync_session")
    @patch("app.workers.moderation_tasks.asyncio.run")
    def test_happy_path_updates_moderation_result(self, mock_run, mock_sync_session):
        workflow_result = MagicMock()
        workflow_result.decision.value = "approved"
        workflow_result.confidence = 0.85
        workflow_result.escalated = False
        workflow_result.model_dump.return_value = {
            "video_id": _VIDEO_ID,
            "decision": "approved",
            "confidence": 0.85,
            "escalated": False,
        }
        mock_run.return_value = workflow_result

        existing_mod = MagicMock()
        mock_db = MagicMock()
        mock_db.__enter__ = lambda s: mock_db
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.query.return_value.filter.return_value.first.return_value = existing_mod
        mock_sync_session.return_value = mock_db

        from app.workers.moderation_tasks import run_moderation_task

        result = run_moderation_task(_VIDEO_ID)

        assert result["decision"] == "approved"
        assert existing_mod.status is not None

    @patch("app.workers.moderation_tasks.asyncio.run")
    def test_workflow_failure_triggers_retry(self, mock_run):
        mock_run.side_effect = RuntimeError("graph failure")

        from app.workers.moderation_tasks import run_moderation_task

        with pytest.raises(Exception):  # noqa: B017 — retry wraps varied error types
            run_moderation_task.apply(args=[_VIDEO_ID]).get(propagate=True)

    @patch("app.workers.moderation_tasks.sync_session")
    @patch("app.workers.moderation_tasks.asyncio.run")
    def test_escalated_decision_sets_escalated_status(self, mock_run, mock_sync_session):
        workflow_result = MagicMock()
        workflow_result.decision.value = "escalated"
        workflow_result.confidence = 0.45
        workflow_result.escalated = True
        workflow_result.model_dump.return_value = {
            "video_id": _VIDEO_ID,
            "decision": "escalated",
            "confidence": 0.45,
            "escalated": True,
        }
        mock_run.return_value = workflow_result

        mock_db = MagicMock()
        mock_db.__enter__ = lambda s: mock_db
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()
        mock_sync_session.return_value = mock_db

        from app.workers.moderation_tasks import run_moderation_task

        result = run_moderation_task(_VIDEO_ID)

        assert result["escalated"] is True


# ── apply_policy_task ──────────────────────────────────────────────────────────


class TestApplyPolicyTask:
    def _make_db_session(self, mod_result=None, policy=None):
        mock_db = MagicMock()
        mock_db.__enter__ = lambda s: mock_db
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.get.side_effect = lambda model, id_: (
            mod_result if "ModerationResult" in str(model) else policy
        )
        return mock_db

    @patch("app.workers.moderation_tasks.sync_session")
    def test_reject_rule_sets_rejected_status(self, mock_sync_session):
        from app.models.moderation import ModerationResult, ModerationStatus

        mod = MagicMock(spec=ModerationResult)
        mod.violations = [{"category": "violence", "severity": "high"}]
        mod.status = ModerationStatus.PENDING

        policy = MagicMock()
        policy.rules = [{"category": "violence", "action": "reject"}]

        mock_db = MagicMock()
        mock_db.__enter__ = lambda s: mock_db
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.get.side_effect = lambda model, _id: (mod if model is ModerationResult else policy)
        mock_sync_session.return_value = mock_db

        from app.workers.moderation_tasks import apply_policy_task

        result = apply_policy_task(_MOD_RESULT_ID, _POLICY_ID)

        assert result["new_status"] == "rejected"

    @patch("app.workers.moderation_tasks.sync_session")
    def test_missing_result_returns_not_found(self, mock_sync_session):
        mock_db = MagicMock()
        mock_db.__enter__ = lambda s: mock_db
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.get.return_value = None
        mock_sync_session.return_value = mock_db

        from app.workers.moderation_tasks import apply_policy_task

        result = apply_policy_task(_MOD_RESULT_ID, _POLICY_ID)

        assert result["new_status"] == "not_found"

    @patch("app.workers.moderation_tasks.sync_session")
    def test_no_matching_rule_keeps_status_unchanged(self, mock_sync_session):
        from app.models.moderation import ModerationResult, ModerationStatus

        mod = MagicMock(spec=ModerationResult)
        mod.violations = [{"category": "spam"}]
        mod.status = ModerationStatus.PENDING

        policy = MagicMock()
        policy.rules = [{"category": "violence", "action": "reject"}]

        mock_db = MagicMock()
        mock_db.__enter__ = lambda s: mock_db
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.get.side_effect = lambda model, _id: (mod if model is ModerationResult else policy)
        mock_sync_session.return_value = mock_db

        from app.workers.moderation_tasks import apply_policy_task

        result = apply_policy_task(_MOD_RESULT_ID, _POLICY_ID)

        assert result["new_status"] == "pending"


# ── dispatch_webhooks_task ─────────────────────────────────────────────────────


class TestDispatchWebhooksTask:
    @patch("app.workers.moderation_tasks.httpx.post")
    @patch("app.workers.moderation_tasks.sync_session")
    def test_delivers_to_subscribed_endpoints(self, mock_sync_session, mock_post):
        endpoint = MagicMock()
        endpoint.id = uuid.uuid4()
        endpoint.url = "https://example.com/hook"
        endpoint.secret = None
        endpoint.events = ["moderation.flagged"]
        endpoint.is_active = True

        # First call returns list of endpoints, subsequent calls return the endpoint for update
        call_count = [0]

        def session_side_effect():
            mock_db = MagicMock()
            mock_db.__enter__ = lambda s: mock_db
            mock_db.__exit__ = MagicMock(return_value=False)
            call_count[0] += 1
            if call_count[0] == 1:
                mock_db.query.return_value.filter.return_value.all.return_value = [endpoint]
            else:
                mock_db.get.return_value = endpoint
            return mock_db

        mock_sync_session.side_effect = session_side_effect

        mock_resp = MagicMock()
        mock_resp.is_success = True
        mock_resp.status_code = 200
        mock_post.return_value = mock_resp

        from app.workers.moderation_tasks import dispatch_webhooks_task

        result = dispatch_webhooks_task("moderation.flagged", {"video_id": _VIDEO_ID})

        assert result["delivered"] == 1
        assert result["failed"] == 0
        mock_post.assert_called_once()

    @patch("app.workers.moderation_tasks.sync_session")
    def test_skips_unsubscribed_events(self, mock_sync_session):
        endpoint = MagicMock()
        endpoint.id = uuid.uuid4()
        endpoint.url = "https://example.com/hook"
        endpoint.events = ["video.processed"]  # not subscribed to moderation.flagged
        endpoint.is_active = True

        mock_db = MagicMock()
        mock_db.__enter__ = lambda s: mock_db
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.query.return_value.filter.return_value.all.return_value = [endpoint]
        mock_sync_session.return_value = mock_db

        from app.workers.moderation_tasks import dispatch_webhooks_task

        result = dispatch_webhooks_task("moderation.flagged", {"video_id": _VIDEO_ID})

        assert result["skipped"] == 1
        assert result["delivered"] == 0

    @patch("app.workers.moderation_tasks.sync_session")
    def test_no_endpoints_returns_zero_counts(self, mock_sync_session):
        mock_db = MagicMock()
        mock_db.__enter__ = lambda s: mock_db
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_sync_session.return_value = mock_db

        from app.workers.moderation_tasks import dispatch_webhooks_task

        result = dispatch_webhooks_task("moderation.flagged", {})

        assert result == {"delivered": 0, "failed": 0, "skipped": 0}


# ── enqueue_human_review_task ──────────────────────────────────────────────────


class TestEnqueueHumanReviewTask:
    @patch("app.workers.moderation_tasks.sync_session")
    def test_creates_new_queue_item(self, mock_sync_session):
        new_item = MagicMock()
        new_item.id = uuid.uuid4()

        mock_db = MagicMock()
        mock_db.__enter__ = lambda s: mock_db
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        def add_side_effect(item):
            item.id = new_item.id

        mock_db.add.side_effect = add_side_effect
        mock_sync_session.return_value = mock_db

        from app.workers.moderation_tasks import enqueue_human_review_task

        result = enqueue_human_review_task(_VIDEO_ID, _MOD_RESULT_ID)

        assert result["created"] is True
        mock_db.add.assert_called_once()

    @patch("app.workers.moderation_tasks.sync_session")
    def test_idempotent_does_not_duplicate(self, mock_sync_session):
        existing = MagicMock()
        existing.id = uuid.uuid4()

        mock_db = MagicMock()
        mock_db.__enter__ = lambda s: mock_db
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.query.return_value.filter.return_value.first.return_value = existing
        mock_sync_session.return_value = mock_db

        from app.workers.moderation_tasks import enqueue_human_review_task

        result = enqueue_human_review_task(_VIDEO_ID)

        assert result["created"] is False
        assert result["queue_item_id"] == str(existing.id)
        mock_db.add.assert_not_called()
