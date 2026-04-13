"""Tests for W-01 — celery_app configuration, routing, and session factory."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestCeleryConfig:
    def test_broker_url_set(self):
        from app.workers.celery_app import celery_app

        assert celery_app.conf.broker_url is not None

    def test_result_backend_set(self):
        from app.workers.celery_app import celery_app

        assert celery_app.conf.result_backend is not None

    def test_task_serializer_is_json(self):
        from app.workers.celery_app import celery_app

        assert celery_app.conf.task_serializer == "json"

    def test_task_acks_late_enabled(self):
        from app.workers.celery_app import celery_app

        assert celery_app.conf.task_acks_late is True

    def test_task_routes_video_queue(self):
        from app.workers.celery_app import celery_app

        routes = celery_app.conf.task_routes
        assert "app.workers.video_tasks.*" in routes
        assert routes["app.workers.video_tasks.*"]["queue"] == "video"

    def test_task_routes_moderation_queue(self):
        from app.workers.celery_app import celery_app

        routes = celery_app.conf.task_routes
        assert routes["app.workers.moderation_tasks.*"]["queue"] == "moderation"

    def test_task_routes_analytics_queue(self):
        from app.workers.celery_app import celery_app

        routes = celery_app.conf.task_routes
        assert routes["app.workers.analytics_tasks.*"]["queue"] == "analytics"

    def test_task_routes_cleanup_queue(self):
        from app.workers.celery_app import celery_app

        routes = celery_app.conf.task_routes
        assert routes["app.workers.cleanup_tasks.*"]["queue"] == "cleanup"

    def test_result_expires_set(self):
        from app.workers.celery_app import celery_app

        assert celery_app.conf.result_expires == 86_400


class TestSyncSession:
    def test_sync_session_commits_on_success(self):
        from app.workers.celery_app import sync_session

        mock_session = MagicMock()
        mock_factory = MagicMock(return_value=mock_session)

        with patch("app.workers.celery_app._SessionFactory", mock_factory), sync_session() as db:
            assert db is mock_session

        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    def test_sync_session_rolls_back_on_exception(self):
        from app.workers.celery_app import sync_session

        mock_session = MagicMock()
        mock_factory = MagicMock(return_value=mock_session)

        with patch("app.workers.celery_app._SessionFactory", mock_factory):
            try:
                with sync_session():
                    raise ValueError("boom")
            except ValueError:
                pass

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
        mock_session.commit.assert_not_called()
