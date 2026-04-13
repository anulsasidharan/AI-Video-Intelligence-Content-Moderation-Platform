"""Tests for W-05 — cleanup_tasks (S3 and DB mocked)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest


def _utc_now():
    return datetime.now(UTC)


# ── cleanup_temp_frames_task ───────────────────────────────────────────────────


class TestCleanupTempFramesTask:
    def _s3_object(self, key: str, age_hours: int = 30):
        return {
            "Key": key,
            "LastModified": _utc_now() - timedelta(hours=age_hours),
        }

    @patch("app.workers.cleanup_tasks.boto3.client")
    def test_deletes_old_objects(self, mock_boto_client):
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3

        old_obj = self._s3_object("temp/frames/old.jpg", age_hours=30)
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{"Contents": [old_obj]}]
        mock_s3.get_paginator.return_value = mock_paginator
        mock_s3.delete_objects.return_value = {"Errors": []}

        from app.workers.cleanup_tasks import cleanup_temp_frames_task

        result = cleanup_temp_frames_task(ttl_hours=24)

        assert result["deleted"] == 1
        assert result["errors"] == 0
        mock_s3.delete_objects.assert_called_once()

    @patch("app.workers.cleanup_tasks.boto3.client")
    def test_skips_recent_objects(self, mock_boto_client):
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3

        recent_obj = self._s3_object("temp/frames/new.jpg", age_hours=1)
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{"Contents": [recent_obj]}]
        mock_s3.get_paginator.return_value = mock_paginator

        from app.workers.cleanup_tasks import cleanup_temp_frames_task

        result = cleanup_temp_frames_task(ttl_hours=24)

        assert result["deleted"] == 0
        mock_s3.delete_objects.assert_not_called()

    @patch("app.workers.cleanup_tasks.boto3.client")
    def test_empty_bucket_returns_zero(self, mock_boto_client):
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3

        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{"Contents": []}]
        mock_s3.get_paginator.return_value = mock_paginator

        from app.workers.cleanup_tasks import cleanup_temp_frames_task

        result = cleanup_temp_frames_task()

        assert result["deleted"] == 0
        assert result["errors"] == 0

    @patch("app.workers.cleanup_tasks.boto3.client")
    def test_s3_error_triggers_retry(self, mock_boto_client):
        mock_boto_client.side_effect = Exception("S3 connection refused")

        from app.workers.cleanup_tasks import cleanup_temp_frames_task

        with pytest.raises(Exception):  # noqa: B017 — retry wraps varied error types
            cleanup_temp_frames_task.apply(args=[24]).get(propagate=True)


# ── purge_stale_jobs_task ──────────────────────────────────────────────────────


class TestPurgeStaleJobsTask:
    @patch("app.workers.cleanup_tasks.sync_session")
    def test_marks_stuck_videos_as_failed(self, mock_sync_session):
        stale_video = MagicMock()
        stale_video.id = uuid.uuid4()

        mock_db = MagicMock()
        mock_db.__enter__ = lambda s: mock_db
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.query.return_value.filter.return_value.all.return_value = [stale_video]
        mock_sync_session.return_value = mock_db

        from app.workers.cleanup_tasks import purge_stale_jobs_task

        result = purge_stale_jobs_task(stale_hours=2)

        assert result["marked_failed"] == 1
        assert "timed out" in stale_video.error_message.lower()

    @patch("app.workers.cleanup_tasks.sync_session")
    def test_no_stale_videos_returns_zero(self, mock_sync_session):
        mock_db = MagicMock()
        mock_db.__enter__ = lambda s: mock_db
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_sync_session.return_value = mock_db

        from app.workers.cleanup_tasks import purge_stale_jobs_task

        result = purge_stale_jobs_task()

        assert result["marked_failed"] == 0

    @patch("app.workers.cleanup_tasks.sync_session")
    def test_db_error_triggers_retry(self, mock_sync_session):
        mock_db = MagicMock()
        mock_db.__enter__ = MagicMock(side_effect=Exception("DB error"))
        mock_sync_session.return_value = mock_db

        from app.workers.cleanup_tasks import purge_stale_jobs_task

        with pytest.raises(Exception):  # noqa: B017 — retry wraps varied error types
            purge_stale_jobs_task.apply().get(propagate=True)


# ── prune_old_analytics_events_task ───────────────────────────────────────────


class TestPruneOldAnalyticsEventsTask:
    @patch("app.workers.cleanup_tasks.sync_session")
    def test_deletes_old_events(self, mock_sync_session):
        mock_db = MagicMock()
        mock_db.__enter__ = lambda s: mock_db
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.query.return_value.filter.return_value.delete.return_value = 42
        mock_sync_session.return_value = mock_db

        from app.workers.cleanup_tasks import prune_old_analytics_events_task

        result = prune_old_analytics_events_task(retention_days=90)

        assert result["deleted"] == 42

    @patch("app.workers.cleanup_tasks.sync_session")
    def test_nothing_to_prune_returns_zero(self, mock_sync_session):
        mock_db = MagicMock()
        mock_db.__enter__ = lambda s: mock_db
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.query.return_value.filter.return_value.delete.return_value = 0
        mock_sync_session.return_value = mock_db

        from app.workers.cleanup_tasks import prune_old_analytics_events_task

        result = prune_old_analytics_events_task()

        assert result["deleted"] == 0


# ── cleanup_orphaned_s3_objects_task ──────────────────────────────────────────


class TestCleanupOrphanedS3ObjectsTask:
    def _s3_object(self, key: str, age_hours: int = 72):
        return {
            "Key": key,
            "LastModified": _utc_now() - timedelta(hours=age_hours),
        }

    @patch("app.workers.cleanup_tasks.sync_session")
    @patch("app.workers.cleanup_tasks.boto3.client")
    def test_deletes_orphaned_objects(self, mock_boto_client, mock_sync_session):
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3

        orphan = self._s3_object("videos/orphan.mp4", age_hours=72)
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{"Contents": [orphan]}]
        mock_s3.get_paginator.return_value = mock_paginator
        mock_s3.delete_objects.return_value = {"Errors": []}

        # No matching video in DB (orphan)
        mock_db = MagicMock()
        mock_db.__enter__ = lambda s: mock_db
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_sync_session.return_value = mock_db

        from app.workers.cleanup_tasks import cleanup_orphaned_s3_objects_task

        result = cleanup_orphaned_s3_objects_task(prefix="videos/", min_age_hours=48)

        assert result["scanned"] == 1
        assert result["deleted"] == 1
        mock_s3.delete_objects.assert_called_once()

    @patch("app.workers.cleanup_tasks.sync_session")
    @patch("app.workers.cleanup_tasks.boto3.client")
    def test_keeps_objects_with_db_record(self, mock_boto_client, mock_sync_session):
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3

        obj = self._s3_object("videos/valid.mp4", age_hours=72)
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{"Contents": [obj]}]
        mock_s3.get_paginator.return_value = mock_paginator

        # Video exists in DB — should NOT be deleted
        mock_db = MagicMock()
        mock_db.__enter__ = lambda s: mock_db
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()
        mock_sync_session.return_value = mock_db

        from app.workers.cleanup_tasks import cleanup_orphaned_s3_objects_task

        result = cleanup_orphaned_s3_objects_task()

        assert result["deleted"] == 0
        mock_s3.delete_objects.assert_not_called()

    @patch("app.workers.cleanup_tasks.sync_session")
    @patch("app.workers.cleanup_tasks.boto3.client")
    def test_skips_objects_newer_than_min_age(self, mock_boto_client, mock_sync_session):
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3

        recent = self._s3_object("videos/recent.mp4", age_hours=10)
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{"Contents": [recent]}]
        mock_s3.get_paginator.return_value = mock_paginator
        mock_sync_session.return_value = MagicMock()

        from app.workers.cleanup_tasks import cleanup_orphaned_s3_objects_task

        result = cleanup_orphaned_s3_objects_task(min_age_hours=48)

        assert result["deleted"] == 0
        mock_s3.delete_objects.assert_not_called()
