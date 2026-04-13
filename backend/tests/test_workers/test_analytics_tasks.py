"""Tests for W-04 — analytics_tasks (DB and Redis mocked)."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

# ── aggregate_daily_stats_task ─────────────────────────────────────────────────


class TestAggregateDailyStatsTask:
    def _mock_db_with_counts(self, videos=3, violations=1, reviews=2, avg_conf=0.75):
        mock_db = MagicMock()
        mock_db.__enter__ = lambda s: mock_db
        mock_db.__exit__ = MagicMock(return_value=False)

        # base = db.query().filter(event_date==...)
        # base.filter(event_type==...).count() — two chained filters
        double_filter = mock_db.query.return_value.filter.return_value.filter.return_value
        double_filter.count.side_effect = [videos, violations, reviews]
        # avg query: db.query(func.avg(...)).filter(...).scalar() — only ONE filter
        mock_db.query.return_value.filter.return_value.scalar.return_value = avg_conf
        return mock_db

    @patch("app.workers.analytics_tasks.sync_session")
    def test_returns_correct_counts(self, mock_sync_session):
        mock_sync_session.return_value = self._mock_db_with_counts(
            videos=5, violations=2, reviews=3, avg_conf=0.82
        )

        from app.workers.analytics_tasks import aggregate_daily_stats_task

        result = aggregate_daily_stats_task(date_str="2026-03-18")

        assert result["date"] == "2026-03-18"
        assert result["videos_processed"] == 5
        assert result["violations_detected"] == 2
        assert result["reviews_completed"] == 3
        assert result["avg_confidence"] == round(0.82, 4)

    @patch("app.workers.analytics_tasks.sync_session")
    def test_uses_yesterday_when_no_date_given(self, mock_sync_session):
        mock_sync_session.return_value = self._mock_db_with_counts()

        from app.workers.analytics_tasks import aggregate_daily_stats_task

        result = aggregate_daily_stats_task()

        # Should not raise and should have a date key
        assert "date" in result

    @patch("app.workers.analytics_tasks.sync_session")
    def test_db_error_triggers_retry(self, mock_sync_session):
        mock_db = MagicMock()
        mock_db.__enter__ = MagicMock(side_effect=Exception("DB connection error"))
        mock_sync_session.return_value = mock_db

        from app.workers.analytics_tasks import aggregate_daily_stats_task

        with pytest.raises(Exception):  # noqa: B017 — retry wraps varied error types
            aggregate_daily_stats_task.apply(args=["2026-03-18"]).get(propagate=True)

    @patch("app.workers.analytics_tasks.sync_session")
    def test_tenant_scoped_result(self, mock_sync_session):
        mock_sync_session.return_value = self._mock_db_with_counts(videos=1)

        from app.workers.analytics_tasks import aggregate_daily_stats_task

        result = aggregate_daily_stats_task(date_str="2026-03-18", tenant_id="tenant-abc")

        assert result["tenant_id"] == "tenant-abc"


# ── compute_policy_effectiveness_task ─────────────────────────────────────────


class TestComputePolicyEffectivenessTask:
    @patch("app.workers.analytics_tasks.sync_session")
    def test_computes_rates(self, mock_sync_session):
        mock_db = MagicMock()
        mock_db.__enter__ = lambda s: mock_db
        mock_db.__exit__ = MagicMock(return_value=False)

        # total=10, approved=7, rejected=2, escalated=1, flagged=0
        mock_db.query.return_value.count.return_value = 10
        mock_db.query.return_value.filter.return_value.count.side_effect = [7, 2, 1, 0]
        mock_sync_session.return_value = mock_db

        policy_id = str(uuid.uuid4())
        from app.workers.analytics_tasks import compute_policy_effectiveness_task

        result = compute_policy_effectiveness_task(policy_id)

        assert result["policy_id"] == policy_id
        assert result["total_evaluated"] == 10
        assert result["approval_rate"] == round(7 / 10, 4)
        assert result["escalation_rate"] == round(1 / 10, 4)

    @patch("app.workers.analytics_tasks.sync_session")
    def test_zero_total_returns_zero_rates(self, mock_sync_session):
        mock_db = MagicMock()
        mock_db.__enter__ = lambda s: mock_db
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.query.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.count.side_effect = [0, 0, 0, 0]
        mock_sync_session.return_value = mock_db

        from app.workers.analytics_tasks import compute_policy_effectiveness_task

        result = compute_policy_effectiveness_task(str(uuid.uuid4()))

        assert result["approval_rate"] == 0.0
        assert result["escalation_rate"] == 0.0


# ── flush_analytics_events_task ───────────────────────────────────────────────


class TestFlushAnalyticsEventsTask:
    @patch("app.workers.analytics_tasks.sync_session")
    @patch("app.workers.analytics_tasks.redis_lib" if False else "redis.from_url")
    def test_flushes_buffered_events(self, *_):
        import json as _json

        events = [
            _json.dumps(
                {
                    "event_type": "video_processed",
                    "video_id": str(uuid.uuid4()),
                    "tenant_id": "t1",
                    "category": None,
                    "confidence": None,
                    "extra": None,
                    "event_date": "2026-03-18",
                }
            ),
        ]

        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline.execute.return_value = (events, None)
        mock_redis.pipeline.return_value = mock_pipeline

        mock_db = MagicMock()
        mock_db.__enter__ = lambda s: mock_db
        mock_db.__exit__ = MagicMock(return_value=False)

        with (
            patch("app.workers.analytics_tasks.sync_session", return_value=mock_db),
            patch("redis.from_url", return_value=mock_redis),
        ):
            from app.workers.analytics_tasks import flush_analytics_events_task

            result = flush_analytics_events_task()

        assert result["flushed"] == 1
        assert result["errors"] == 0
        mock_db.add_all.assert_called_once()

    @patch("app.workers.analytics_tasks.sync_session")
    def test_malformed_event_counted_as_error(self, mock_sync_session):
        mock_db = MagicMock()
        mock_db.__enter__ = lambda s: mock_db
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_sync_session.return_value = mock_db

        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline.execute.return_value = (["not-valid-json-{{{"], None)
        mock_redis.pipeline.return_value = mock_pipeline

        with patch("redis.from_url", return_value=mock_redis):
            from app.workers.analytics_tasks import flush_analytics_events_task

            result = flush_analytics_events_task()

        assert result["errors"] == 1
        assert result["flushed"] == 0

    def test_empty_buffer_returns_zero(self):
        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline.execute.return_value = ([], None)
        mock_redis.pipeline.return_value = mock_pipeline

        mock_db = MagicMock()
        mock_db.__enter__ = lambda s: mock_db
        mock_db.__exit__ = MagicMock(return_value=False)

        with (
            patch("app.workers.analytics_tasks.sync_session", return_value=mock_db),
            patch("redis.from_url", return_value=mock_redis),
        ):
            from app.workers.analytics_tasks import flush_analytics_events_task

            result = flush_analytics_events_task()

        assert result["flushed"] == 0
        assert result["errors"] == 0
