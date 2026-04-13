"""Tests for /api/v1/policies endpoints."""

import pytest
from httpx import AsyncClient

POLICIES_URL = "/api/v1/policies"

_POLICY_PAYLOAD = {
    "name": "Default Policy",
    "description": "Blocks violence and nudity",
    "is_active": True,
    "is_default": False,
    "rules": [
        {"category": "violence", "threshold": 0.8, "action": "block"},
        {"category": "nudity", "threshold": 0.7, "action": "flag"},
    ],
    "default_action": "allow",
}


@pytest.mark.asyncio
async def test_list_policies_empty(client: AsyncClient, admin_token: str) -> None:
    resp = await client.get(POLICIES_URL, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.json()["data"]["items"] == []


@pytest.mark.asyncio
async def test_create_policy(client: AsyncClient, admin_token: str) -> None:
    resp = await client.post(
        POLICIES_URL,
        json=_POLICY_PAYLOAD,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["name"] == "Default Policy"
    assert len(data["rules"]) == 2


@pytest.mark.asyncio
async def test_get_policy(client: AsyncClient, admin_token: str) -> None:
    created = await client.post(
        POLICIES_URL,
        json=_POLICY_PAYLOAD,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    policy_id = created.json()["data"]["id"]

    resp = await client.get(
        f"{POLICIES_URL}/{policy_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == policy_id


@pytest.mark.asyncio
async def test_update_policy(client: AsyncClient, admin_token: str) -> None:
    created = await client.post(
        POLICIES_URL,
        json=_POLICY_PAYLOAD,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    policy_id = created.json()["data"]["id"]

    resp = await client.put(
        f"{POLICIES_URL}/{policy_id}",
        json={"name": "Updated Policy"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "Updated Policy"


@pytest.mark.asyncio
async def test_delete_policy(client: AsyncClient, admin_token: str) -> None:
    created = await client.post(
        POLICIES_URL,
        json=_POLICY_PAYLOAD,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    policy_id = created.json()["data"]["id"]

    resp = await client.delete(
        f"{POLICIES_URL}/{policy_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_unauthenticated(client: AsyncClient) -> None:
    resp = await client.get(POLICIES_URL)
    assert resp.status_code == 401
