"""Tests for S-06 NotificationService — DB and HTTP mocked."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import NotFoundError, ValidationError

# ── Helpers ────────────────────────────────────────────────────────────────────

_OWNER_ID = uuid.uuid4()
_ENDPOINT_ID = uuid.uuid4()


def _make_endpoint(endpoint_id=None, url="https://example.com/hook", secret="mysecret"):
    e = MagicMock()
    e.id = endpoint_id or _ENDPOINT_ID
    e.url = url
    e.secret = secret
    e.events = ["moderation.flagged"]
    e.is_active = True
    e.owner_id = _OWNER_ID
    e.tenant_id = None
    e.total_deliveries = 0
    e.failed_deliveries = 0
    e.last_delivery_at = None
    e.last_status_code = None
    e.created_at = None
    return e


def _make_db(endpoint=None):
    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = endpoint
    result_mock.scalar_one.return_value = 0
    result_mock.scalars.return_value.all.return_value = [endpoint] if endpoint else []
    db.execute = AsyncMock(return_value=result_mock)
    db.scalar = AsyncMock(return_value=0)
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.delete = AsyncMock()
    return db


# ── list_webhooks ──────────────────────────────────────────────────────────────


class TestListWebhooks:
    @pytest.mark.asyncio
    async def test_returns_list_response(self):
        from app.services.notification_service import NotificationService

        endpoint = _make_endpoint()
        db = _make_db(endpoint=endpoint)

        mock_list_resp = MagicMock()
        with (
            patch("app.services.notification_service.WebhookResponse") as MockResp,
            patch(
                "app.services.notification_service.WebhookListResponse",
                return_value=mock_list_resp,
            ),
        ):
            MockResp.model_validate.return_value = MagicMock()
            service = NotificationService(db=db)
            result = await service.list_webhooks(_OWNER_ID)

        assert result is mock_list_resp


# ── create_webhook ─────────────────────────────────────────────────────────────


class TestCreateWebhook:
    @pytest.mark.asyncio
    async def test_creates_endpoint(self):
        from app.schemas.webhook import WebhookCreate
        from app.services.notification_service import NotificationService

        db = _make_db(endpoint=None)
        endpoint = _make_endpoint()

        body = MagicMock(spec=WebhookCreate)
        body.url = "https://example.com/hook"
        body.secret = "mysecret"
        body.events = ["moderation.flagged"]
        body.is_active = True

        with (
            patch(
                "app.services.notification_service.WebhookEndpoint",
                return_value=endpoint,
            ),
            patch("app.services.notification_service.WebhookResponse") as MockResp,
        ):
            MockResp.model_validate.return_value = MagicMock()
            service = NotificationService(db=db)
            await service.create_webhook(_OWNER_ID, None, body)

        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_raises_validation_error_for_unknown_event(self):
        from app.schemas.webhook import WebhookCreate
        from app.services.notification_service import NotificationService

        db = _make_db()
        body = MagicMock(spec=WebhookCreate)
        body.events = ["not.a.real.event"]

        service = NotificationService(db=db)
        with pytest.raises(ValidationError):
            await service.create_webhook(_OWNER_ID, None, body)


# ── get_webhook ────────────────────────────────────────────────────────────────


class TestGetWebhook:
    @pytest.mark.asyncio
    async def test_returns_webhook_for_owner(self):
        from app.services.notification_service import NotificationService

        endpoint = _make_endpoint()
        db = _make_db(endpoint=endpoint)

        with patch("app.services.notification_service.WebhookResponse") as MockResp:
            MockResp.model_validate.return_value = MagicMock()
            service = NotificationService(db=db)
            await service.get_webhook(_ENDPOINT_ID, _OWNER_ID)

    @pytest.mark.asyncio
    async def test_raises_not_found_when_missing(self):
        from app.services.notification_service import NotificationService

        db = _make_db(endpoint=None)
        service = NotificationService(db=db)
        with pytest.raises(NotFoundError):
            await service.get_webhook(uuid.uuid4(), _OWNER_ID)


# ── delete_webhook ─────────────────────────────────────────────────────────────


class TestDeleteWebhook:
    @pytest.mark.asyncio
    async def test_deletes_endpoint(self):
        from app.services.notification_service import NotificationService

        endpoint = _make_endpoint()
        db = _make_db(endpoint=endpoint)

        service = NotificationService(db=db)
        await service.delete_webhook(_ENDPOINT_ID)
        db.delete.assert_awaited_once_with(endpoint)

    @pytest.mark.asyncio
    async def test_raises_not_found_when_missing(self):
        from app.services.notification_service import NotificationService

        db = _make_db(endpoint=None)
        service = NotificationService(db=db)
        with pytest.raises(NotFoundError):
            await service.delete_webhook(uuid.uuid4())


# ── test_webhook ───────────────────────────────────────────────────────────────


class TestTestWebhook:
    @pytest.mark.asyncio
    async def test_sends_ping_and_records_delivery(self):
        from app.services.notification_service import NotificationService

        endpoint = _make_endpoint()
        db = _make_db(endpoint=endpoint)

        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=mock_response)
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "app.services.notification_service.httpx.AsyncClient",
            return_value=mock_http,
        ):
            service = NotificationService(db=db)
            result = await service.test_webhook(_ENDPOINT_ID)

        assert "200" in result
        assert endpoint.total_deliveries == 1

    @pytest.mark.asyncio
    async def test_returns_failure_message_on_request_error(self):
        import httpx

        from app.services.notification_service import NotificationService

        endpoint = _make_endpoint()
        db = _make_db(endpoint=endpoint)

        mock_http = AsyncMock()
        mock_http.post = AsyncMock(side_effect=httpx.RequestError("connection refused"))
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "app.services.notification_service.httpx.AsyncClient",
            return_value=mock_http,
        ):
            service = NotificationService(db=db)
            result = await service.test_webhook(_ENDPOINT_ID)

        assert "failed" in result.lower()
        assert endpoint.failed_deliveries == 1


# ── dispatch_event ─────────────────────────────────────────────────────────────


class TestDispatchEvent:
    def test_enqueues_celery_task(self):
        from app.services.notification_service import NotificationService

        db = MagicMock()
        with patch("app.workers.moderation_tasks.dispatch_webhooks_task") as mock_task:
            mock_task.delay = MagicMock()
            service = NotificationService(db=db)
            service.dispatch_event("moderation.flagged", {"video_id": "abc"}, tenant_id="t1")

        mock_task.delay.assert_called_once_with(
            event="moderation.flagged",
            payload={"video_id": "abc"},
            tenant_id="t1",
        )
