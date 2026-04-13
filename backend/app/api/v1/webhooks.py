"""
Webhooks API — B-07
Register, manage, and test outbound webhook endpoints.
"""

import hashlib
import hmac
import json
import uuid
from datetime import UTC, datetime
from typing import Annotated

import httpx
import structlog
from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AdminUser, CurrentUser
from app.core.exceptions import NotFoundError, ValidationError
from app.dependencies import get_db
from app.models.webhook import SUPPORTED_EVENTS, WebhookEndpoint
from app.schemas.webhook import (
    MessageResponse,
    WebhookCreate,
    WebhookListResponse,
    WebhookResponse,
    WebhookUpdate,
)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = structlog.get_logger(__name__)


def _sign_payload(secret: str, payload: bytes) -> str:
    """HMAC-SHA256 signature for webhook delivery verification."""
    return "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


# ── GET /webhooks ─────────────────────────────────────────────────────────────


@router.get("", response_model=WebhookListResponse, summary="List registered webhook endpoints")
async def list_webhooks(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WebhookListResponse:
    q = select(WebhookEndpoint).where(WebhookEndpoint.owner_id == current_user.id)
    total = await db.scalar(select(func.count()).select_from(q.subquery())) or 0
    result = await db.execute(q.order_by(WebhookEndpoint.created_at.desc()))
    endpoints = result.scalars().all()

    return WebhookListResponse(
        items=[WebhookResponse.model_validate(e) for e in endpoints],
        total=total,
    )


# ── POST /webhooks ────────────────────────────────────────────────────────────


@router.post(
    "",
    response_model=WebhookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new webhook endpoint",
)
async def create_webhook(
    body: WebhookCreate,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WebhookResponse:
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
        owner_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )
    db.add(endpoint)
    await db.flush()

    logger.info("webhook_created", endpoint_id=str(endpoint.id), url=str(body.url))
    return WebhookResponse.model_validate(endpoint)


# ── GET /webhooks/{id} ────────────────────────────────────────────────────────


@router.get(
    "/{endpoint_id}",
    response_model=WebhookResponse,
    summary="Get webhook detail and delivery stats",
)
async def get_webhook(
    endpoint_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WebhookResponse:
    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.id == endpoint_id,
            WebhookEndpoint.owner_id == current_user.id,
        )
    )
    endpoint = result.scalar_one_or_none()
    if not endpoint:
        raise NotFoundError("WebhookEndpoint", str(endpoint_id))
    return WebhookResponse.model_validate(endpoint)


# ── PUT /webhooks/{id} ────────────────────────────────────────────────────────


@router.put(
    "/{endpoint_id}",
    response_model=WebhookResponse,
    summary="Update a webhook endpoint",
)
async def update_webhook(
    endpoint_id: uuid.UUID,
    body: WebhookUpdate,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WebhookResponse:
    result = await db.execute(select(WebhookEndpoint).where(WebhookEndpoint.id == endpoint_id))
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
            raise ValidationError(f"Unsupported events: {invalid}", {"supported": SUPPORTED_EVENTS})
        endpoint.events = body.events
    if body.is_active is not None:
        endpoint.is_active = body.is_active

    logger.info("webhook_updated", endpoint_id=str(endpoint_id))
    return WebhookResponse.model_validate(endpoint)


# ── DELETE /webhooks/{id} ─────────────────────────────────────────────────────


@router.delete(
    "/{endpoint_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Delete a webhook endpoint",
)
async def delete_webhook(
    endpoint_id: uuid.UUID,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    result = await db.execute(select(WebhookEndpoint).where(WebhookEndpoint.id == endpoint_id))
    endpoint = result.scalar_one_or_none()
    if not endpoint:
        raise NotFoundError("WebhookEndpoint", str(endpoint_id))
    await db.delete(endpoint)
    logger.info("webhook_deleted", endpoint_id=str(endpoint_id))


# ── POST /webhooks/test/{id} ──────────────────────────────────────────────────


@router.post(
    "/test/{endpoint_id}",
    response_model=MessageResponse,
    summary="Send a test payload to the webhook URL",
)
async def test_webhook(
    endpoint_id: uuid.UUID,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    result = await db.execute(select(WebhookEndpoint).where(WebhookEndpoint.id == endpoint_id))
    endpoint = result.scalar_one_or_none()
    if not endpoint:
        raise NotFoundError("WebhookEndpoint", str(endpoint_id))

    payload_dict = {
        "event": "test",
        "timestamp": datetime.now(UTC).isoformat(),
        "endpoint_id": str(endpoint_id),
    }
    payload_bytes = json.dumps(payload_dict).encode()

    headers = {"Content-Type": "application/json", "X-VidShield-Event": "test"}
    if endpoint.secret:
        headers["X-VidShield-Signature"] = _sign_payload(endpoint.secret, payload_bytes)

    try:
        async with httpx.AsyncClient(timeout=10.0) as http:
            response = await http.post(endpoint.url, content=payload_bytes, headers=headers)

        endpoint.total_deliveries += 1
        endpoint.last_delivery_at = datetime.now(UTC).isoformat()
        endpoint.last_status_code = response.status_code
        if response.status_code >= 400:
            endpoint.failed_deliveries += 1

        logger.info(
            "webhook_test_sent",
            endpoint_id=str(endpoint_id),
            status=response.status_code,
        )
        return MessageResponse(message=f"Test payload delivered. HTTP {response.status_code}.")

    except httpx.RequestError as exc:
        endpoint.failed_deliveries += 1
        logger.warning("webhook_test_failed", endpoint_id=str(endpoint_id), error=str(exc))
        return MessageResponse(message=f"Delivery failed: {exc}")
