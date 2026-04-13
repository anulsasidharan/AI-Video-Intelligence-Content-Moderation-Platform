"""
S-06 NotificationService

Manages outbound webhook endpoints (CRUD) and event dispatch.
Synchronous fan-out to Celery; async test delivery via httpx.

Public API:
    await service.list_webhooks(owner_id)                      -> WebhookListResponse
    await service.create_webhook(owner_id, tenant_id, body)    -> WebhookResponse
    await service.get_webhook(endpoint_id, owner_id)           -> WebhookResponse
    await service.update_webhook(endpoint_id, body)            -> WebhookResponse
    await service.delete_webhook(endpoint_id)                  -> None
    await service.test_webhook(endpoint_id)                    -> str  (status message)
          service.dispatch_event(event, payload, tenant_id)    -> None  (enqueues Celery task)
"""

from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from datetime import UTC, datetime
from typing import Any

import httpx
import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.webhook import SUPPORTED_EVENTS, WebhookEndpoint
from app.schemas.webhook import (
    WebhookCreate,
    WebhookListResponse,
    WebhookResponse,
    WebhookUpdate,
)

logger = structlog.get_logger(__name__)

_WEBHOOK_TEST_TIMEOUT = 10.0


def _sign_payload(secret: str, payload: bytes) -> str:
    """Compute HMAC-SHA256 signature for webhook payload verification."""
    return "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


class NotificationService:
    """Webhook CRUD and event dispatch service."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── CRUD ───────────────────────────────────────────────────────────────────

    async def list_webhooks(self, owner_id: uuid.UUID) -> WebhookListResponse:
        """
        List all webhook endpoints belonging to an owner.

        Args:
            owner_id: UUID of the requesting user.

        Returns:
            WebhookListResponse schema.
        """
        q = select(WebhookEndpoint).where(WebhookEndpoint.owner_id == owner_id)
        total = await self._db.scalar(select(func.count()).select_from(q.subquery())) or 0
        result = await self._db.execute(q.order_by(WebhookEndpoint.created_at.desc()))
        endpoints = result.scalars().all()

        return WebhookListResponse(
            items=[WebhookResponse.model_validate(e) for e in endpoints],
            total=total,
        )

    async def create_webhook(
        self,
        owner_id: uuid.UUID,
        tenant_id: str | None,
        body: WebhookCreate,
    ) -> WebhookResponse:
        """
        Register a new webhook endpoint.

        Raises:
            ValidationError: If any subscribed event name is not in SUPPORTED_EVENTS.

        Returns:
            WebhookResponse for the created endpoint.
        """
        invalid = [e for e in body.events if e not in SUPPORTED_EVENTS]
        if invalid:
            raise ValidationError(
                f"Unsupported events: {invalid}",
                {"supported": SUPPORTED_EVENTS},
            )

        endpoint = WebhookEndpoint(
            url=str(body.url),
            secret=body.secret,
            events=body.events,
            is_active=body.is_active,
            owner_id=owner_id,
            tenant_id=tenant_id,
        )
        self._db.add(endpoint)
        await self._db.flush()

        logger.info("webhook_created", endpoint_id=str(endpoint.id), url=str(body.url))
        return WebhookResponse.model_validate(endpoint)

    async def get_webhook(
        self,
        endpoint_id: uuid.UUID,
        owner_id: uuid.UUID,
    ) -> WebhookResponse:
        """
        Fetch a single webhook endpoint owned by the requesting user.

        Raises:
            NotFoundError: If the endpoint doesn't exist or isn't owned by the user.
        """
        result = await self._db.execute(
            select(WebhookEndpoint).where(
                WebhookEndpoint.id == endpoint_id,
                WebhookEndpoint.owner_id == owner_id,
            )
        )
        endpoint = result.scalar_one_or_none()
        if not endpoint:
            raise NotFoundError("WebhookEndpoint", str(endpoint_id))

        return WebhookResponse.model_validate(endpoint)

    async def update_webhook(
        self,
        endpoint_id: uuid.UUID,
        body: WebhookUpdate,
    ) -> WebhookResponse:
        """
        Update webhook URL, secret, event list, or active flag.

        Raises:
            NotFoundError:  If the endpoint doesn't exist.
            ValidationError: If any new event name is unsupported.
        """
        result = await self._db.execute(
            select(WebhookEndpoint).where(WebhookEndpoint.id == endpoint_id)
        )
        endpoint = result.scalar_one_or_none()
        if not endpoint:
            raise NotFoundError("WebhookEndpoint", str(endpoint_id))

        if body.url is not None:
            endpoint.url = str(body.url)
        if body.secret is not None:
            endpoint.secret = body.secret
        if body.events is not None:
            invalid = [e for e in body.events if e not in SUPPORTED_EVENTS]
            if invalid:
                raise ValidationError(
                    f"Unsupported events: {invalid}",
                    {"supported": SUPPORTED_EVENTS},
                )
            endpoint.events = body.events
        if body.is_active is not None:
            endpoint.is_active = body.is_active

        logger.info("webhook_updated", endpoint_id=str(endpoint_id))
        return WebhookResponse.model_validate(endpoint)

    async def delete_webhook(self, endpoint_id: uuid.UUID) -> None:
        """
        Permanently delete a webhook endpoint.

        Raises:
            NotFoundError: If the endpoint doesn't exist.
        """
        result = await self._db.execute(
            select(WebhookEndpoint).where(WebhookEndpoint.id == endpoint_id)
        )
        endpoint = result.scalar_one_or_none()
        if not endpoint:
            raise NotFoundError("WebhookEndpoint", str(endpoint_id))

        await self._db.delete(endpoint)
        logger.info("webhook_deleted", endpoint_id=str(endpoint_id))

    # ── Test delivery ──────────────────────────────────────────────────────────

    async def test_webhook(self, endpoint_id: uuid.UUID) -> str:
        """
        Send a test `ping` payload to the endpoint's URL.

        Returns:
            Human-readable delivery status message.

        Raises:
            NotFoundError: If the endpoint doesn't exist.
        """
        result = await self._db.execute(
            select(WebhookEndpoint).where(WebhookEndpoint.id == endpoint_id)
        )
        endpoint = result.scalar_one_or_none()
        if not endpoint:
            raise NotFoundError("WebhookEndpoint", str(endpoint_id))

        payload_dict: dict[str, Any] = {
            "event": "test",
            "timestamp": datetime.now(UTC).isoformat(),
            "endpoint_id": str(endpoint_id),
        }
        payload_bytes = json.dumps(payload_dict).encode()

        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "X-VidShield-Event": "test",
        }
        if endpoint.secret:
            headers["X-VidShield-Signature"] = _sign_payload(endpoint.secret, payload_bytes)

        try:
            async with httpx.AsyncClient(timeout=_WEBHOOK_TEST_TIMEOUT) as http:
                response = await http.post(endpoint.url, content=payload_bytes, headers=headers)

            endpoint.total_deliveries += 1
            endpoint.last_delivery_at = datetime.now(UTC).isoformat()
            endpoint.last_status_code = response.status_code
            if response.status_code >= 400:
                endpoint.failed_deliveries += 1

            logger.info(
                "webhook_test_sent",
                endpoint_id=str(endpoint_id),
                status_code=response.status_code,
            )
            return f"Test payload delivered. HTTP {response.status_code}."

        except httpx.RequestError as exc:
            endpoint.failed_deliveries += 1
            logger.warning("webhook_test_failed", endpoint_id=str(endpoint_id), error=str(exc))
            return f"Delivery failed: {exc}"

    # ── Event dispatch ─────────────────────────────────────────────────────────

    def dispatch_event(
        self,
        event: str,
        payload: dict[str, Any],
        tenant_id: str | None = None,
    ) -> None:
        """
        Fan-out an event to all subscribed active webhook endpoints via Celery.

        This is a synchronous call that enqueues a Celery task — it does not
        block on delivery. Suitable for calling from async FastAPI routes.

        Args:
            event:     Event name, e.g. "moderation.flagged".
            payload:   JSON-serializable event payload.
            tenant_id: Optional tenant scope — only deliver to matching endpoints.
        """
        from app.workers.moderation_tasks import dispatch_webhooks_task

        dispatch_webhooks_task.delay(event=event, payload=payload, tenant_id=tenant_id)
        logger.info("webhook_event_dispatched", webhook_event=event, tenant_id=tenant_id)
