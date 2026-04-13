from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import socketio
from fastapi import APIRouter, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.api.v1 import agent_audit
from app.api.v1.router import api_router
from app.config import settings
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.logging import setup_logging
from app.core.middleware import (
    DataWrapperMiddleware,
    RateLimitMiddleware,
    RequestContextMiddleware,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    # Eagerly initialise the DB connection pool and Redis client so the
    # first real request is not hit with cold-start latency.
    from app.dependencies import get_engine, get_redis_client

    get_engine()
    get_redis_client()
    yield
    # Cleanup on shutdown (close DB engine, Redis pool, etc.)
    from app.dependencies import _engine, _redis

    if _engine:
        await _engine.dispose()
    if _redis:
        await _redis.aclose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description="AI Video Intelligence & Content Moderation Platform — Backend API",
        version="0.1.0",
        docs_url="/docs" if settings.APP_ENV != "production" else None,
        redoc_url="/redoc" if settings.APP_ENV != "production" else None,
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    # ── Middleware ────────────────────────────────────────────────────────────
    # NOTE: Starlette middleware stack runs in reverse registration order.
    # Outer → Inner: CORS → RateLimit → RequestContext → DataWrapper
    app.add_middleware(DataWrapperMiddleware)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception handlers ────────────────────────────────────────────────────
    app.add_exception_handler(AppException, app_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(api_router)

    # Non-versioned admin alias (same handlers as /api/v1/admin/agent-audit)
    _admin_api_alias = APIRouter(prefix="/api")
    _admin_api_alias.include_router(agent_audit.router_alias)
    app.include_router(_admin_api_alias)

    # ── Health check ──────────────────────────────────────────────────────────
    @app.get("/health", tags=["ops"], include_in_schema=False)
    async def health() -> dict:
        return {"status": "ok", "env": settings.APP_ENV}

    return app


app = create_app()

# ── Socket.IO ─────────────────────────────────────────────────────────────────
# Wraps the FastAPI ASGI app so /socket.io/ requests are handled by Socket.IO
# and everything else passes through to FastAPI.
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=settings.CORS_ORIGINS,
    logger=False,
    engineio_logger=False,
)


@sio.event
async def connect(sid: str, environ: dict, auth: dict | None = None) -> None:  # noqa: ARG001
    pass


@sio.event
async def disconnect(sid: str) -> None:  # noqa: ARG001
    pass


@sio.event
async def join(sid: str, data: dict) -> None:
    room = data.get("room")
    if room:
        await sio.enter_room(sid, room)


@sio.event
async def leave(sid: str, data: dict) -> None:
    room = data.get("room")
    if room:
        await sio.leave_room(sid, room)


asgi_app = socketio.ASGIApp(sio, other_asgi_app=app)
