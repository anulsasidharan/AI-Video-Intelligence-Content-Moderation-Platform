"""Tests for app.core.middleware — request context and response wrapping."""

import uuid

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.middleware import DataWrapperMiddleware, RequestContextMiddleware


def _make_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(DataWrapperMiddleware)
    app.add_middleware(RequestContextMiddleware)

    @app.get("/simple")
    async def simple():
        return {"key": "value"}

    @app.get("/already-wrapped-data")
    async def already_wrapped_data():
        return {"data": {"nested": True}}

    @app.get("/already-wrapped-error")
    async def already_wrapped_error():
        return {"error": {"code": "X", "message": "y"}}

    @app.get("/list-response")
    async def list_response():
        return [1, 2, 3]

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


@pytest.fixture(scope="module")
async def ac():
    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


# ── RequestContextMiddleware ──────────────────────────────────────────────────


@pytest.mark.anyio
async def test_request_id_header_present(ac: AsyncClient):
    r = await ac.get("/simple")
    assert "x-request-id" in r.headers


@pytest.mark.anyio
async def test_request_id_is_uuid_format(ac: AsyncClient):
    r = await ac.get("/simple")
    uid = r.headers["x-request-id"]
    uuid.UUID(uid)  # raises ValueError if not a valid UUID


@pytest.mark.anyio
async def test_each_request_gets_unique_id(ac: AsyncClient):
    r1 = await ac.get("/simple")
    r2 = await ac.get("/simple")
    assert r1.headers["x-request-id"] != r2.headers["x-request-id"]


# ── DataWrapperMiddleware ─────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_simple_response_wrapped(ac: AsyncClient):
    r = await ac.get("/simple")
    assert r.status_code == 200
    body = r.json()
    assert "data" in body
    assert body["data"] == {"key": "value"}


@pytest.mark.anyio
async def test_already_data_wrapped_not_double_wrapped(ac: AsyncClient):
    r = await ac.get("/already-wrapped-data")
    body = r.json()
    # Should not produce {"data": {"data": {...}}}
    assert "data" in body
    assert "data" not in body.get("data", {})


@pytest.mark.anyio
async def test_error_envelope_not_wrapped(ac: AsyncClient):
    r = await ac.get("/already-wrapped-error")
    body = r.json()
    assert "error" in body
    assert "data" not in body


@pytest.mark.anyio
async def test_list_response_wrapped(ac: AsyncClient):
    r = await ac.get("/list-response")
    body = r.json()
    assert body["data"] == [1, 2, 3]


@pytest.mark.anyio
async def test_skip_path_not_wrapped(ac: AsyncClient):
    r = await ac.get("/health")
    body = r.json()
    # /health is in _SKIP_PATHS — response must not be wrapped
    assert "data" not in body
    assert body == {"status": "ok"}
