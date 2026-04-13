"""Tests for /api/v1/auth endpoints."""

import pytest
from httpx import AsyncClient

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
REFRESH_URL = "/api/v1/auth/refresh"
LOGOUT_URL = "/api/v1/auth/logout"
ME_URL = "/api/v1/auth/me"

_TEST_EMAIL = "test@vidshield.ai"
_TEST_PASSWORD = "securepassword123"
_TEST_PAYLOAD = {"name": "Test User", "email": _TEST_EMAIL, "password": _TEST_PASSWORD}


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient) -> None:
    resp = await client.post(REGISTER_URL, json=_TEST_PAYLOAD)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["user"]["email"] == _TEST_EMAIL
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient) -> None:
    await client.post(REGISTER_URL, json=_TEST_PAYLOAD)
    resp = await client.post(REGISTER_URL, json=_TEST_PAYLOAD)
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_register_short_password(client: AsyncClient) -> None:
    resp = await client.post(
        REGISTER_URL, json={"name": "Test", "email": _TEST_EMAIL, "password": "short"}
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient) -> None:
    await client.post(REGISTER_URL, json=_TEST_PAYLOAD)
    resp = await client.post(LOGIN_URL, json={"email": _TEST_EMAIL, "password": _TEST_PASSWORD})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["user"]["email"] == _TEST_EMAIL
    assert "access_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient) -> None:
    await client.post(REGISTER_URL, json=_TEST_PAYLOAD)
    resp = await client.post(LOGIN_URL, json={"email": _TEST_EMAIL, "password": "wrongpassword"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_login_unknown_user(client: AsyncClient) -> None:
    resp = await client.post(LOGIN_URL, json={"email": "nobody@test.com", "password": "pass1234"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_success(client: AsyncClient) -> None:
    reg = await client.post(REGISTER_URL, json=_TEST_PAYLOAD)
    refresh_token = reg.json()["data"]["refresh_token"]
    resp = await client.post(REFRESH_URL, json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_refresh_invalid_token(client: AsyncClient) -> None:
    resp = await client.post(REFRESH_URL, json={"refresh_token": "bad.token.here"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_authenticated(client: AsyncClient) -> None:
    reg = await client.post(REGISTER_URL, json=_TEST_PAYLOAD)
    access_token = reg.json()["data"]["access_token"]
    resp = await client.get(ME_URL, headers={"Authorization": f"Bearer {access_token}"})
    assert resp.status_code == 200
    assert resp.json()["data"]["email"] == _TEST_EMAIL


@pytest.mark.asyncio
async def test_me_unauthenticated(client: AsyncClient) -> None:
    resp = await client.get(ME_URL)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_logout_invalidates_refresh_token(client: AsyncClient) -> None:
    reg = await client.post(REGISTER_URL, json=_TEST_PAYLOAD)
    tokens = reg.json()["data"]
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    resp = await client.post(
        LOGOUT_URL,
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert resp.status_code == 200

    # Refresh token should now be revoked
    resp2 = await client.post(REFRESH_URL, json={"refresh_token": refresh_token})
    assert resp2.status_code == 401
