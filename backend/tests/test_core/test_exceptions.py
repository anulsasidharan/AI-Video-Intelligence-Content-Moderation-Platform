"""Tests for app.core.exceptions — error envelope shape and HTTP status codes."""

import json
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from httpx import ASGITransport, AsyncClient

from app.core.exceptions import (
    AppException,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
    app_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)

# ── Helper: minimal app with registered handlers ──────────────────────────────


def _make_app() -> FastAPI:
    test_app = FastAPI()
    test_app.add_exception_handler(AppException, app_exception_handler)
    test_app.add_exception_handler(RequestValidationError, validation_exception_handler)
    test_app.add_exception_handler(Exception, unhandled_exception_handler)

    @test_app.get("/not-found")
    async def raise_not_found():
        raise NotFoundError("Video", "abc-123")

    @test_app.get("/unauthorized")
    async def raise_unauthorized():
        raise UnauthorizedError()

    @test_app.get("/forbidden")
    async def raise_forbidden():
        raise ForbiddenError()

    @test_app.get("/conflict")
    async def raise_conflict():
        raise ConflictError("Resource already exists.")

    @test_app.get("/validation")
    async def raise_validation():
        raise ValidationError("Bad value", details={"field": "email"})

    @test_app.get("/validate-body")
    async def validate_body(q: int):  # int param from query string forces validation
        return {"q": q}

    return test_app


@pytest.fixture(scope="module")
async def ac():
    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


# ── Error envelope structure ──────────────────────────────────────────────────


@pytest.mark.anyio
async def test_not_found_status_and_envelope(ac: AsyncClient):
    r = await ac.get("/not-found")
    assert r.status_code == 404
    body = r.json()
    assert "error" in body
    assert body["error"]["code"] == "NOT_FOUND"
    assert "Video" in body["error"]["message"]
    assert "abc-123" in body["error"]["message"]


@pytest.mark.anyio
async def test_unauthorized_status(ac: AsyncClient):
    r = await ac.get("/unauthorized")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.anyio
async def test_forbidden_status(ac: AsyncClient):
    r = await ac.get("/forbidden")
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "FORBIDDEN"


@pytest.mark.anyio
async def test_conflict_status(ac: AsyncClient):
    r = await ac.get("/conflict")
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "CONFLICT"


@pytest.mark.anyio
async def test_validation_error_status(ac: AsyncClient):
    r = await ac.get("/validation")
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"
    assert r.json()["error"]["details"]["field"] == "email"


@pytest.mark.anyio
async def test_unhandled_exception_handler_returns_500_directly():
    """Unit-test the handler function directly; bypasses FastAPI's ServerErrorMiddleware
    which re-raises raw RuntimeError before custom Exception handlers can intercept."""
    mock_request = MagicMock(spec=Request)
    response = await unhandled_exception_handler(mock_request, RuntimeError("unexpected boom"))
    assert response.status_code == 500
    body = json.loads(response.body)
    assert body["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert "boom" not in response.body.decode()


@pytest.mark.anyio
async def test_pydantic_validation_envelope(ac: AsyncClient):
    r = await ac.get("/validate-body?q=not-an-int")
    assert r.status_code == 422
    body = r.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "fields" in body["error"]["details"]


# ── Unit: AppException attributes ────────────────────────────────────────────


def test_app_exception_defaults():
    exc = AppException(status_code=400, code="BAD_REQUEST", message="bad")
    assert exc.status_code == 400
    assert exc.details == {}


def test_app_exception_with_details():
    exc = AppException(400, "BAD", "msg", details={"k": "v"})
    assert exc.details == {"k": "v"}
