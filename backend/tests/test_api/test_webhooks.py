"""Tests for /api/v1/webhooks endpoints."""

import pytest
from httpx import AsyncClient

WEBHOOKS_URL = "/api/v1/webhooks"

_WEBHOOK_PAYLOAD = {
    "url": "https://example.com/webhook",
    "secret": "mysecret",
    "events": ["video.processed", "moderation.flagged"],
    "is_active": True,
}


@pytest.mark.asyncio
async def test_list_webhooks_empty(client: AsyncClient, admin_token: str) -> None:
    resp = await client.get(WEBHOOKS_URL, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.json()["data"]["items"] == []


@pytest.mark.asyncio
async def test_create_webhook(client: AsyncClient, admin_token: str) -> None:
    resp = await client.post(
        WEBHOOKS_URL,
        json=_WEBHOOK_PAYLOAD,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["url"] == "https://example.com/webhook"
    assert "video.processed" in data["events"]


@pytest.mark.asyncio
async def test_create_webhook_invalid_event(client: AsyncClient, admin_token: str) -> None:
    resp = await client.post(
        WEBHOOKS_URL,
        json={**_WEBHOOK_PAYLOAD, "events": ["invalid.event"]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_webhook(client: AsyncClient, admin_token: str) -> None:
    created = await client.post(
        WEBHOOKS_URL,
        json=_WEBHOOK_PAYLOAD,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    wid = created.json()["data"]["id"]

    resp = await client.get(
        f"{WEBHOOKS_URL}/{wid}", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == wid


@pytest.mark.asyncio
async def test_update_webhook(client: AsyncClient, admin_token: str) -> None:
    created = await client.post(
        WEBHOOKS_URL,
        json=_WEBHOOK_PAYLOAD,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    wid = created.json()["data"]["id"]

    resp = await client.put(
        f"{WEBHOOKS_URL}/{wid}",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["is_active"] is False


@pytest.mark.asyncio
async def test_delete_webhook(client: AsyncClient, admin_token: str) -> None:
    created = await client.post(
        WEBHOOKS_URL,
        json=_WEBHOOK_PAYLOAD,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    wid = created.json()["data"]["id"]

    resp = await client.delete(
        f"{WEBHOOKS_URL}/{wid}", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 204

    resp2 = await client.get(
        f"{WEBHOOKS_URL}/{wid}", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp2.status_code == 404


@pytest.mark.asyncio
async def test_unauthenticated(client: AsyncClient) -> None:
    resp = await client.get(WEBHOOKS_URL)
    assert resp.status_code == 401
