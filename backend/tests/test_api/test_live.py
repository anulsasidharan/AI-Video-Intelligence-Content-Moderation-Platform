"""Tests for /api/v1/live endpoints."""

import pytest
from httpx import AsyncClient

STREAMS_URL = "/api/v1/live/streams"


async def _get_token(client: AsyncClient) -> str:
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Live User",
            "email": "liveuser@test.com",
            "password": "password1234",
        },
    )
    return resp.json()["data"]["access_token"]


@pytest.mark.asyncio
async def test_list_streams_empty(client: AsyncClient) -> None:
    token = await _get_token(client)
    resp = await client.get(STREAMS_URL, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["data"]["items"] == []


@pytest.mark.asyncio
async def test_create_stream(client: AsyncClient) -> None:
    token = await _get_token(client)
    resp = await client.post(
        STREAMS_URL,
        json={"title": "My Live Stream"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["title"] == "My Live Stream"
    assert data["status"] == "active"
    assert "ingest_url" in data


@pytest.mark.asyncio
async def test_get_stream_not_found(client: AsyncClient) -> None:
    token = await _get_token(client)
    resp = await client.get(
        f"{STREAMS_URL}/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_stop_stream(client: AsyncClient) -> None:
    token = await _get_token(client)
    created = await client.post(
        STREAMS_URL,
        json={"title": "Stream to Stop"},
        headers={"Authorization": f"Bearer {token}"},
    )
    stream_id = created.json()["data"]["id"]

    resp = await client.post(
        f"{STREAMS_URL}/{stream_id}/stop",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert "stopped" in resp.json()["data"]["message"].lower()


@pytest.mark.asyncio
async def test_unauthenticated(client: AsyncClient) -> None:
    resp = await client.get(STREAMS_URL)
    assert resp.status_code == 401
