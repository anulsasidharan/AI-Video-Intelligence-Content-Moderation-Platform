"""Tests for /api/v1/moderation endpoints."""

import pytest
from httpx import AsyncClient

QUEUE_URL = "/api/v1/moderation/queue"


async def _get_operator_token(client: AsyncClient) -> str:
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Operator User",
            "email": "operator@test.com",
            "password": "password1234",
        },
    )
    return resp.json()["data"]["access_token"]


@pytest.mark.asyncio
async def test_list_queue_empty(client: AsyncClient) -> None:
    token = await _get_operator_token(client)
    resp = await client.get(QUEUE_URL, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_get_moderation_result_not_found(client: AsyncClient) -> None:
    token = await _get_operator_token(client)
    resp = await client.get(
        "/api/v1/moderation/videos/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_unauthenticated_queue(client: AsyncClient) -> None:
    resp = await client.get(QUEUE_URL)
    assert resp.status_code == 401
