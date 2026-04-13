"""Tests for D-07 WebhookEndpoint model."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from app.models.user import User
from app.models.webhook import WebhookEndpoint


def _make_user(db_session):
    u = User(email=f"u{uuid.uuid4()}@test.ai", password_hash="hash")
    db_session.add(u)
    return u


class TestWebhookEndpointModel:
    @pytest.mark.asyncio
    async def test_create_webhook_with_defaults(self, db_session):
        owner = _make_user(db_session)
        await db_session.flush()

        webhook = WebhookEndpoint(
            url="https://example.com/webhook",
            owner_id=owner.id,
        )
        db_session.add(webhook)
        await db_session.flush()

        result = await db_session.execute(
            select(WebhookEndpoint).where(WebhookEndpoint.owner_id == owner.id)
        )
        w = result.scalar_one()

        assert w.is_active is True
        assert w.total_deliveries == 0
        assert w.failed_deliveries == 0
        assert w.secret is None
        assert w.last_delivery_at is None

    @pytest.mark.asyncio
    async def test_webhook_events_stored_as_json(self, db_session):
        owner = _make_user(db_session)
        await db_session.flush()

        events = ["moderation.completed", "video.processed", "alert.created"]
        webhook = WebhookEndpoint(
            url="https://example.com/events",
            owner_id=owner.id,
            events=events,
        )
        db_session.add(webhook)
        await db_session.flush()

        result = await db_session.execute(
            select(WebhookEndpoint).where(WebhookEndpoint.url == "https://example.com/events")
        )
        w = result.scalar_one()

        assert isinstance(w.events, list)
        assert "moderation.completed" in w.events

    @pytest.mark.asyncio
    async def test_webhook_delivery_stats(self, db_session):
        owner = _make_user(db_session)
        await db_session.flush()

        webhook = WebhookEndpoint(
            url="https://example.com/stats",
            owner_id=owner.id,
            total_deliveries=10,
            failed_deliveries=2,
            last_delivery_at="2024-01-01T12:00:00Z",
            last_status_code=200,
        )
        db_session.add(webhook)
        await db_session.flush()

        result = await db_session.execute(
            select(WebhookEndpoint).where(WebhookEndpoint.url == "https://example.com/stats")
        )
        w = result.scalar_one()

        assert w.total_deliveries == 10
        assert w.failed_deliveries == 2
        assert w.last_status_code == 200

    @pytest.mark.asyncio
    async def test_webhook_with_secret(self, db_session):
        owner = _make_user(db_session)
        await db_session.flush()

        webhook = WebhookEndpoint(
            url="https://example.com/secure",
            owner_id=owner.id,
            secret="whsec_supersecretvalue",
        )
        db_session.add(webhook)
        await db_session.flush()

        result = await db_session.execute(
            select(WebhookEndpoint).where(WebhookEndpoint.url == "https://example.com/secure")
        )
        w = result.scalar_one()
        assert w.secret == "whsec_supersecretvalue"
