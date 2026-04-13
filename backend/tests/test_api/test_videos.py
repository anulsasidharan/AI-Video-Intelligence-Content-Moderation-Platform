"""Tests for /api/v1/videos endpoints."""

import pytest
from httpx import AsyncClient

VIDEOS_URL = "/api/v1/videos"
UPLOAD_URL_ENDPOINT = "/api/v1/videos/upload-url"


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _get_token(client: AsyncClient) -> str:
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Video User",
            "email": "videouser@test.com",
            "password": "password1234",
        },
    )
    return resp.json()["data"]["access_token"]


async def _create_video(client: AsyncClient, token: str, title: str = "Test Video") -> dict:
    resp = await client.post(
        VIDEOS_URL,
        json={"title": title, "s3_key": "uploads/test/file.mp4"},
        headers={"Authorization": f"Bearer {token}"},
    )
    return resp.json()["data"]


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_videos_empty(client: AsyncClient) -> None:
    token = await _get_token(client)
    resp = await client.get(VIDEOS_URL, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_create_video(client: AsyncClient) -> None:
    token = await _get_token(client)
    resp = await client.post(
        VIDEOS_URL,
        json={
            "title": "My Video",
            "s3_key": "uploads/test/video.mp4",
            "tags": ["cats", "fun"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["title"] == "My Video"
    assert data["status"] == "pending"
    assert data["tags"] == ["cats", "fun"]


@pytest.mark.asyncio
async def test_get_upload_url(client: AsyncClient) -> None:
    token = await _get_token(client)
    resp = await client.post(
        UPLOAD_URL_ENDPOINT,
        json={"filename": "myvideo.mp4", "content_type": "video/mp4"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "upload_url" in data
    assert "s3_key" in data
    assert data["expires_in"] > 0


@pytest.mark.asyncio
async def test_get_video(client: AsyncClient) -> None:
    token = await _get_token(client)
    created = await _create_video(client, token)
    vid_id = created["id"]

    resp = await client.get(f"{VIDEOS_URL}/{vid_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == vid_id


@pytest.mark.asyncio
async def test_get_video_not_found(client: AsyncClient) -> None:
    token = await _get_token(client)
    resp = await client.get(
        f"{VIDEOS_URL}/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_video(client: AsyncClient) -> None:
    token = await _get_token(client)
    created = await _create_video(client, token)
    vid_id = created["id"]

    resp = await client.put(
        f"{VIDEOS_URL}/{vid_id}",
        json={"title": "Updated Title"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["title"] == "Updated Title"


@pytest.mark.asyncio
async def test_list_videos_pagination(client: AsyncClient) -> None:
    token = await _get_token(client)
    for i in range(3):
        await _create_video(client, token, title=f"Video {i}")

    resp = await client.get(
        f"{VIDEOS_URL}?page=1&page_size=2",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total"] == 3
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_video_status(client: AsyncClient) -> None:
    token = await _get_token(client)
    created = await _create_video(client, token)
    vid_id = created["id"]

    resp = await client.get(
        f"{VIDEOS_URL}/{vid_id}/status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "pending"


@pytest.mark.asyncio
async def test_unauthenticated_request(client: AsyncClient) -> None:
    resp = await client.get(VIDEOS_URL)
    assert resp.status_code == 401
