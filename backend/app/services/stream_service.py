"""
S-07 StreamService

Live stream lifecycle management: registration, status transitions,
WebSocket event broadcast, and Redis pub/sub.

Public API:
    await service.list_streams(tenant_id, active_only)         -> StreamListResponse
    await service.create_stream(owner_id, tenant_id, body)     -> StreamResponse
    await service.get_stream(stream_id)                        -> StreamResponse
    await service.stop_stream(stream_id)                       -> None
    await service.broadcast_event(stream_id, event_name, data) -> None
    await service.subscribe_websocket(stream_id, websocket, token) -> None
"""

from __future__ import annotations

import contextlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any

import redis.asyncio as aioredis
import structlog
from fastapi import WebSocket, WebSocketDisconnect
from jose import JWTError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import NotFoundError
from app.core.security import decode_token
from app.models.alert import LiveStream, StreamStatus
from app.schemas.live import StreamCreate, StreamListResponse, StreamResponse

logger = structlog.get_logger(__name__)

# In-memory WebSocket registry: {stream_id: [WebSocket, ...]}
# Shared at module level so all service instances see the same connections.
_ws_connections: dict[str, list[WebSocket]] = {}

_REDIS_CHANNEL_PREFIX = "stream"


class StreamService:
    """Live stream management and real-time event broadcasting."""

    def __init__(self, db: AsyncSession, redis: aioredis.Redis) -> None:
        self._db = db
        self._redis = redis

    # ── List ───────────────────────────────────────────────────────────────────

    async def list_streams(
        self,
        tenant_id: str | None = None,
        active_only: bool = True,
    ) -> StreamListResponse:
        """
        Return all live streams, optionally filtered by tenant and active status.

        Args:
            tenant_id:   Tenant scope.
            active_only: If True, return only ACTIVE streams.

        Returns:
            StreamListResponse schema.
        """
        q = select(LiveStream)
        if tenant_id:
            q = q.where(LiveStream.tenant_id == tenant_id)
        if active_only:
            q = q.where(LiveStream.status == StreamStatus.ACTIVE)

        total_result = await self._db.execute(select(func.count()).select_from(q.subquery()))
        total = total_result.scalar_one()

        result = await self._db.execute(q.order_by(LiveStream.created_at.desc()))
        streams = result.scalars().all()

        return StreamListResponse(
            items=[StreamResponse.model_validate(s) for s in streams],
            total=total,
        )

    # ── Create ─────────────────────────────────────────────────────────────────

    async def create_stream(
        self,
        owner_id: uuid.UUID,
        tenant_id: str | None,
        body: StreamCreate,
    ) -> StreamResponse:
        """
        Register a new live stream and generate an RTMP ingest URL.

        Args:
            owner_id:  UUID of the operator creating the stream.
            tenant_id: Tenant scope.
            body:      StreamCreate schema with title and optional metadata.

        Returns:
            StreamResponse with the ingest URL and stream key.
        """
        stream_id = uuid.uuid4()
        ingest_url = f"rtmp://{settings.RTMP_INGEST_HOST}/live/{stream_id}"

        stream = LiveStream(
            id=stream_id,
            title=body.title,
            ingest_url=ingest_url,
            status=StreamStatus.ACTIVE,
            owner_id=owner_id,
            tenant_id=tenant_id,
        )
        self._db.add(stream)
        await self._db.flush()

        logger.info("stream_created", stream_id=str(stream_id), owner_id=str(owner_id))
        return StreamResponse.model_validate(stream)

    # ── Read ───────────────────────────────────────────────────────────────────

    async def get_stream(self, stream_id: uuid.UUID) -> StreamResponse:
        """
        Fetch a live stream by ID.

        Raises:
            NotFoundError: If the stream doesn't exist.
        """
        result = await self._db.execute(select(LiveStream).where(LiveStream.id == stream_id))
        stream = result.scalar_one_or_none()
        if not stream:
            raise NotFoundError("LiveStream", str(stream_id))

        return StreamResponse.model_validate(stream)

    # ── Stop ───────────────────────────────────────────────────────────────────

    async def stop_stream(self, stream_id: uuid.UUID) -> None:
        """
        Transition a stream to STOPPED status and broadcast a stop event.

        Raises:
            NotFoundError: If the stream doesn't exist.
        """
        result = await self._db.execute(select(LiveStream).where(LiveStream.id == stream_id))
        stream = result.scalar_one_or_none()
        if not stream:
            raise NotFoundError("LiveStream", str(stream_id))

        stream.status = StreamStatus.STOPPED
        stream.stopped_at = datetime.now(UTC).isoformat()

        await self.broadcast_event(stream_id, "stream.stopped", {"stream_id": str(stream_id)})
        logger.info("stream_stopped", stream_id=str(stream_id))

    # ── Broadcast ──────────────────────────────────────────────────────────────

    async def broadcast_event(
        self,
        stream_id: uuid.UUID,
        event_name: str,
        data: dict[str, Any],
    ) -> None:
        """
        Push a JSON event to all WebSocket clients watching a stream
        AND publish to the Redis pub/sub channel for the stream.

        Args:
            stream_id:  UUID of the stream.
            event_name: Event label, e.g. "frame.alert", "stream.stopped".
            data:       Arbitrary event payload dict.
        """
        sid = str(stream_id)
        message = json.dumps({"event": event_name, **data})

        # Broadcast to in-memory WebSocket connections
        if sid in _ws_connections:
            dead: list[WebSocket] = []
            for ws in list(_ws_connections[sid]):
                try:
                    await ws.send_text(message)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                with contextlib.suppress(ValueError):
                    _ws_connections[sid].remove(ws)

        # Publish to Redis channel
        channel = f"{_REDIS_CHANNEL_PREFIX}:{sid}:events"
        await self._redis.publish(channel, message)

    # ── WebSocket handler ──────────────────────────────────────────────────────

    async def subscribe_websocket(
        self,
        stream_id: str,
        websocket: WebSocket,
        token: str,
    ) -> None:
        """
        Authenticate, register, and manage a WebSocket connection lifecycle.

        Protocol:
        - Client sends "ping" → server responds "pong"
        - Server pushes events via broadcast_event()
        - Connection cleaned up on disconnect

        Args:
            stream_id: Stream ID string from URL path parameter.
            websocket: FastAPI WebSocket instance.
            token:     JWT access token (passed as query parameter).

        Raises:
            Closes with code 4001 on invalid token.
        """
        try:
            payload = decode_token(token)
            if payload.get("type") != "access":
                await websocket.close(code=4001)
                return
        except JWTError:
            await websocket.close(code=4001)
            return

        await websocket.accept()
        sid = stream_id

        if sid not in _ws_connections:
            _ws_connections[sid] = []
        _ws_connections[sid].append(websocket)
        logger.info("ws_client_connected", stream_id=sid, user_sub=payload.get("sub"))

        try:
            while True:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
        except WebSocketDisconnect:
            logger.info("ws_client_disconnected", stream_id=sid)
        finally:
            if sid in _ws_connections:
                with contextlib.suppress(ValueError):
                    _ws_connections[sid].remove(websocket)
