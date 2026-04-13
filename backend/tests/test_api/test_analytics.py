"""Tests for /api/v1/analytics endpoints."""

import pytest
from httpx import AsyncClient


async def _get_token(client: AsyncClient) -> str:
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Analytics User",
            "email": "analytics@test.com",
            "password": "password1234",
        },
    )
    return resp.json()["data"]["access_token"]


@pytest.mark.asyncio
async def test_summary_empty(client: AsyncClient) -> None:
    token = await _get_token(client)
    resp = await client.get(
        "/api/v1/analytics/summary", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total_videos_processed"] == 0
    assert data["total_violations_detected"] == 0
    assert data["violation_rate_percent"] == 0.0


@pytest.mark.asyncio
async def test_violations_empty(client: AsyncClient) -> None:
    token = await _get_token(client)
    resp = await client.get(
        "/api/v1/analytics/violations", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["time_series"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_export_csv(client: AsyncClient) -> None:
    token = await _get_token(client)
    resp = await client.get(
        "/api/v1/analytics/export", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]


@pytest.mark.asyncio
async def test_unauthenticated(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/analytics/summary")
    assert resp.status_code == 401
