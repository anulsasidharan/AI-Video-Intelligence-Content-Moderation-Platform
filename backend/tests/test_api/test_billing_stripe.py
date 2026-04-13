"""Tests for Stripe payment gateway integration.

All Stripe SDK calls are mocked — no real network requests are made.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.billing import UserSubscription

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_stripe_sig(payload: bytes, secret: str) -> str:
    """Produce a valid Stripe-Signature header value for testing."""
    ts = int(time.time())
    signed_payload = f"{ts}.{payload.decode()}"
    sig = hmac.new(secret.encode(), signed_payload.encode(), hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


async def _register_and_login(client: AsyncClient) -> tuple[str, str]:
    email = f"stripe-test-{uuid.uuid4().hex[:8]}@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={"name": "Stripe Test", "email": email, "password": "testpass123"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "testpass123"},
    )
    user_id = login.json()["data"]["user"]["id"]
    token = login.json()["data"]["access_token"]
    return token, user_id


# ── Checkout session ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_checkout_session_starter(client: AsyncClient) -> None:
    token, _ = await _register_and_login(client)

    mock_session = MagicMock()
    mock_session.__getitem__ = lambda self, k: {
        "id": "cs_test_starter",
        "url": "https://checkout.stripe.com/test/starter",
    }[k]

    mock_customer = MagicMock()
    mock_customer.__getitem__ = lambda self, k: {"id": "cus_test123"}[k]

    with (
        patch("stripe.Customer.create", return_value=mock_customer),
        patch("stripe.checkout.Session.create", return_value=mock_session),
    ):
        resp = await client.post(
            "/api/v1/billing/checkout",
            json={"plan": "starter"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200, resp.text
    assert "checkout_url" in resp.json()["data"]
    assert resp.json()["data"]["checkout_url"] == "https://checkout.stripe.com/test/starter"


@pytest.mark.asyncio
async def test_checkout_session_growth(client: AsyncClient) -> None:
    token, _ = await _register_and_login(client)

    mock_session = MagicMock()
    mock_session.__getitem__ = lambda self, k: {
        "id": "cs_test_growth",
        "url": "https://checkout.stripe.com/test/growth",
    }[k]

    mock_customer = MagicMock()
    mock_customer.__getitem__ = lambda self, k: {"id": "cus_test456"}[k]

    with (
        patch("stripe.Customer.create", return_value=mock_customer),
        patch("stripe.checkout.Session.create", return_value=mock_session),
    ):
        resp = await client.post(
            "/api/v1/billing/checkout",
            json={"plan": "growth"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    assert resp.json()["data"]["checkout_url"] == "https://checkout.stripe.com/test/growth"


@pytest.mark.asyncio
async def test_checkout_session_free_plan_rejected(client: AsyncClient) -> None:
    token, _ = await _register_and_login(client)

    resp = await client.post(
        "/api/v1/billing/checkout",
        json={"plan": "free"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_checkout_session_enterprise_rejected(client: AsyncClient) -> None:
    token, _ = await _register_and_login(client)

    resp = await client.post(
        "/api/v1/billing/checkout",
        json={"plan": "enterprise"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_checkout_session_unknown_plan_rejected(client: AsyncClient) -> None:
    token, _ = await _register_and_login(client)

    resp = await client.post(
        "/api/v1/billing/checkout",
        json={"plan": "ultra"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


# ── Portal session ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_portal_session(client: AsyncClient) -> None:
    token, _ = await _register_and_login(client)

    mock_portal = MagicMock()
    mock_portal.__getitem__ = lambda self, k: {"url": "https://billing.stripe.com/test/portal"}[k]

    mock_customer = MagicMock()
    mock_customer.__getitem__ = lambda self, k: {"id": "cus_portal123"}[k]

    with (
        patch("stripe.Customer.create", return_value=mock_customer),
        patch("stripe.billing_portal.Session.create", return_value=mock_portal),
    ):
        resp = await client.post(
            "/api/v1/billing/portal",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    assert resp.json()["data"]["portal_url"] == "https://billing.stripe.com/test/portal"


# ── Webhook: checkout.session.completed ───────────────────────────────────────


@pytest.mark.asyncio
async def test_webhook_checkout_completed(client: AsyncClient, db_session: AsyncSession) -> None:
    _, user_id = await _register_and_login(client)

    # Seed a subscription row with a stripe_customer_id
    sub = await db_session.scalar(
        select(UserSubscription).where(UserSubscription.user_id == uuid.UUID(user_id))
    )
    if sub is None:
        sub = UserSubscription(
            user_id=uuid.UUID(user_id),
            plan_key="free",
            status="active",
            stripe_customer_id="cus_webhook_test",
        )
        db_session.add(sub)
    else:
        sub.stripe_customer_id = "cus_webhook_test"
    await db_session.commit()

    subscription_obj: dict = {
        "id": "sub_test123",
        "customer": "cus_webhook_test",
        "status": "active",
        "current_period_end": int(time.time()) + 2592000,
        "metadata": {"user_id": user_id, "plan_key": "starter"},
    }
    mock_subscription = MagicMock()
    mock_subscription.__getitem__ = lambda self, k: subscription_obj[k]
    mock_subscription.get = lambda k, d=None: subscription_obj.get(k, d)

    payload_data = {
        "id": "evt_checkout_completed",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_completed",
                "subscription": "sub_test123",
                "customer": "cus_webhook_test",
            }
        },
    }
    payload_bytes = json.dumps(payload_data).encode()

    mock_event = MagicMock()
    mock_event.__getitem__ = lambda self, k: payload_data[k]

    with (
        patch("stripe.Webhook.construct_event", return_value=mock_event),
        patch("stripe.Subscription.retrieve", return_value=mock_subscription),
    ):
        resp = await client.post(
            "/api/v1/billing/webhook",
            content=payload_bytes,
            headers={
                "stripe-signature": "t=1,v1=test",
                "Content-Type": "application/json",
            },
        )

    assert resp.status_code == 200
    data = resp.json()
    received = data.get("received") or data.get("data", {}).get("received")
    assert received is True


# ── Webhook: invoice.paid ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_webhook_invoice_paid(client: AsyncClient, db_session: AsyncSession) -> None:
    _, user_id = await _register_and_login(client)

    sub = await db_session.scalar(
        select(UserSubscription).where(UserSubscription.user_id == uuid.UUID(user_id))
    )
    if sub is None:
        sub = UserSubscription(
            user_id=uuid.UUID(user_id),
            plan_key="starter",
            status="active",
            stripe_customer_id="cus_invoice_test",
        )
        db_session.add(sub)
    else:
        sub.stripe_customer_id = "cus_invoice_test"
        sub.plan_key = "starter"
    await db_session.commit()

    invoice_obj: dict = {
        "id": "in_test123",
        "number": "INV-TEST-001",
        "customer": "cus_invoice_test",
        "status": "paid",
        "amount_paid": 29900,
        "currency": "usd",
        "created": int(time.time()),
        "payment_intent": "pi_test123",
        "status_transitions": {"paid_at": int(time.time())},
    }
    payload_data = {
        "id": "evt_invoice_paid",
        "type": "invoice.paid",
        "data": {"object": invoice_obj},
    }
    payload_bytes = json.dumps(payload_data).encode()

    mock_event = MagicMock()
    mock_event.__getitem__ = lambda self, k: payload_data[k]

    with patch("stripe.Webhook.construct_event", return_value=mock_event):
        resp = await client.post(
            "/api/v1/billing/webhook",
            content=payload_bytes,
            headers={
                "stripe-signature": "t=1,v1=test",
                "Content-Type": "application/json",
            },
        )

    assert resp.status_code == 200


# ── Webhook: subscription.deleted ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_webhook_subscription_deleted(client: AsyncClient, db_session: AsyncSession) -> None:
    _, user_id = await _register_and_login(client)

    sub = await db_session.scalar(
        select(UserSubscription).where(UserSubscription.user_id == uuid.UUID(user_id))
    )
    if sub is None:
        sub = UserSubscription(
            user_id=uuid.UUID(user_id),
            plan_key="starter",
            status="active",
            stripe_customer_id="cus_delete_test",
        )
        db_session.add(sub)
    else:
        sub.stripe_customer_id = "cus_delete_test"
        sub.plan_key = "starter"
    await db_session.commit()

    payload_data = {
        "id": "evt_sub_deleted",
        "type": "customer.subscription.deleted",
        "data": {
            "object": {
                "id": "sub_deleted",
                "customer": "cus_delete_test",
                "status": "canceled",
                "metadata": {},
            }
        },
    }
    payload_bytes = json.dumps(payload_data).encode()

    mock_event = MagicMock()
    mock_event.__getitem__ = lambda self, k: payload_data[k]

    with patch("stripe.Webhook.construct_event", return_value=mock_event):
        resp = await client.post(
            "/api/v1/billing/webhook",
            content=payload_bytes,
            headers={
                "stripe-signature": "t=1,v1=test",
                "Content-Type": "application/json",
            },
        )

    assert resp.status_code == 200

    await db_session.refresh(sub)
    assert sub.plan_key == "free"
    assert sub.status == "canceled"


# ── Webhook: invalid signature ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_webhook_invalid_signature(client: AsyncClient) -> None:
    import stripe as _stripe

    with patch(
        "stripe.Webhook.construct_event",
        side_effect=_stripe.error.SignatureVerificationError("bad", "bad"),
    ):
        resp = await client.post(
            "/api/v1/billing/webhook",
            content=b'{"type":"test"}',
            headers={
                "stripe-signature": "t=bad,v1=bad",
                "Content-Type": "application/json",
            },
        )

    assert resp.status_code == 400
