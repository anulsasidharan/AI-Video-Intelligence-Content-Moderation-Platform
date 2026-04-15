"""
Live Stream API — B-05

Stream registration, management, real-time moderation control,
and WebSocket event streaming.

New in this revision:
  POST /live/streams/{id}/start-moderation  — activate frame analysis
  POST /live/streams/{id}/stop-moderation   — deactivate frame analysis
  POST /live/streams/{id}/frames            — submit frame batch for analysis
  GET  /live/streams/{id}/alerts            — list alerts for a stream
  WS   /live/ws/streams/{id}               — real-time moderation events
                                              (via Redis pub/sub bridge)
"""

import asyncio
import contextlib
import json
import uuid
from datetime import UTC, datetime
from typing import Annotated

import structlog
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from jose import JWTError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, OperatorUser
from app.config import settings
from app.core.exceptions import NotFoundError
from app.core.security import decode_token
from app.dependencies import get_db, get_redis
from app.models.alert import Alert, LiveStream, StreamStatus
from app.schemas.live import (
    AlertListResponse,
    AlertResponse,
    FrameSubmitRequest,
    MessageResponse,
    StreamCreate,
    StreamListResponse,
    StreamResponse,
)

router = APIRouter(prefix="/live", tags=["live"])
logger = structlog.get_logger(__name__)

# Frame-rate limiter key prefix in Redis: live:rl:{stream_id}
_FRAME_RL_KEY = "live:rl:{sid}"
_FRAME_RL_MAX = 10  # max POST /frames requests per stream per 10-second window
_FRAME_RL_WIN = 10  # seconds


# ── GET /live/streams ─────────────────────────────────────────────────────────


@router.get("/streams", response_model=StreamListResponse, summary="List live streams")
async def list_streams(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    active_only: bool = Query(True),
) -> StreamListResponse:
    q = select(LiveStream)
    if current_user.tenant_id:
        q = q.where(LiveStream.tenant_id == current_user.tenant_id)
    if active_only:
        q = q.where(LiveStream.status == StreamStatus.ACTIVE)

    total_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_result.scalar_one()
    result = await db.execute(q.order_by(LiveStream.created_at.desc()))
    streams = result.scalars().all()

    return StreamListResponse(
        items=[StreamResponse.model_validate(s) for s in streams],
        total=total,
    )


# ── POST /live/streams ────────────────────────────────────────────────────────


@router.post(
    "/streams",
    response_model=StreamResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register and start a new live stream",
)
async def create_stream(
    body: StreamCreate,
    current_user: OperatorUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StreamResponse:
    stream_id = uuid.uuid4()
    ingest_url = f"rtmp://{settings.RTMP_INGEST_HOST}/live/{stream_id}"

    stream = LiveStream(
        id=stream_id,
        title=body.title,
        ingest_url=ingest_url,
        status=StreamStatus.ACTIVE,
        owner_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )
    db.add(stream)
    await db.flush()
    logger.info("stream_created", stream_id=str(stream_id))
    return StreamResponse.model_validate(stream)


# ── GET /live/streams/{id} ────────────────────────────────────────────────────


@router.get(
    "/streams/{stream_id}",
    response_model=StreamResponse,
    summary="Get live stream detail",
)
async def get_stream(
    stream_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StreamResponse:
    result = await db.execute(select(LiveStream).where(LiveStream.id == stream_id))
    stream = result.scalar_one_or_none()
    if not stream:
        raise NotFoundError("LiveStream", str(stream_id))
    return StreamResponse.model_validate(stream)


# ── POST /live/streams/{id}/stop ──────────────────────────────────────────────


@router.post(
    "/streams/{stream_id}/stop",
    response_model=MessageResponse,
    summary="Stop an active live stream",
)
async def stop_stream(
    stream_id: uuid.UUID,
    current_user: OperatorUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis=Depends(get_redis),  # noqa: B008
) -> MessageResponse:
    result = await db.execute(select(LiveStream).where(LiveStream.id == stream_id))
    stream = result.scalar_one_or_none()
    if not stream:
        raise NotFoundError("LiveStream", str(stream_id))

    stream.status = StreamStatus.STOPPED
    stream.moderation_active = False
    stream.moderation_stopped_at = datetime.now(UTC)
    stream.stopped_at = datetime.now(UTC).isoformat()
    await db.flush()

    # Notify WebSocket clients
    event = json.dumps({"event": "stream.stopped", "stream_id": str(stream_id)})
    await redis.publish(f"live:events:{stream_id}", event)

    logger.info("stream_stopped", stream_id=str(stream_id))
    return MessageResponse(message="Stream stopped successfully.")


# ── POST /live/streams/{id}/start-moderation ─────────────────────────────────


@router.post(
    "/streams/{stream_id}/start-moderation",
    response_model=StreamResponse,
    summary="Activate real-time AI moderation for a live stream",
)
async def start_moderation(
    stream_id: uuid.UUID,
    current_user: OperatorUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis=Depends(get_redis),  # noqa: B008
) -> StreamResponse:
    result = await db.execute(select(LiveStream).where(LiveStream.id == stream_id))
    stream = result.scalar_one_or_none()
    if not stream:
        raise NotFoundError("LiveStream", str(stream_id))
    if stream.status != StreamStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Stream must be active to start moderation.")

    stream.moderation_active = True
    stream.moderation_started_at = datetime.now(UTC)
    stream.moderation_stopped_at = None
    await db.flush()

    event = json.dumps({"event": "moderation.started", "stream_id": str(stream_id)})
    await redis.publish(f"live:events:{stream_id}", event)

    logger.info("stream_moderation_started", stream_id=str(stream_id))
    return StreamResponse.model_validate(stream)


# ── POST /live/streams/{id}/stop-moderation ──────────────────────────────────


@router.post(
    "/streams/{stream_id}/stop-moderation",
    response_model=StreamResponse,
    summary="Deactivate real-time AI moderation (stream stays active)",
)
async def stop_moderation(
    stream_id: uuid.UUID,
    current_user: OperatorUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis=Depends(get_redis),  # noqa: B008
) -> StreamResponse:
    result = await db.execute(select(LiveStream).where(LiveStream.id == stream_id))
    stream = result.scalar_one_or_none()
    if not stream:
        raise NotFoundError("LiveStream", str(stream_id))

    stream.moderation_active = False
    stream.moderation_stopped_at = datetime.now(UTC)
    await db.flush()

    event = json.dumps({"event": "moderation.stopped", "stream_id": str(stream_id)})
    await redis.publish(f"live:events:{stream_id}", event)

    logger.info("stream_moderation_stopped", stream_id=str(stream_id))
    return StreamResponse.model_validate(stream)


# ── POST /live/streams/{id}/frames ────────────────────────────────────────────


@router.post(
    "/streams/{stream_id}/frames",
    response_model=MessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit captured frames for live moderation analysis",
)
async def submit_frames(
    stream_id: uuid.UUID,
    body: FrameSubmitRequest,
    current_user: OperatorUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis=Depends(get_redis),  # noqa: B008
) -> MessageResponse:
    """
    Accept a batch of base64-encoded JPEG frames from the browser capture loop
    and queue them for AI analysis.

    Rate limited: max 10 POSTs per stream per 10-second window to prevent
    runaway resource consumption.
    """
    result = await db.execute(select(LiveStream).where(LiveStream.id == stream_id))
    stream = result.scalar_one_or_none()
    if not stream:
        raise NotFoundError("LiveStream", str(stream_id))
    if not stream.moderation_active:
        raise HTTPException(status_code=409, detail="Moderation is not active for this stream.")

    # Per-stream frame submission rate limit
    sid = str(stream_id)
    rl_key = _FRAME_RL_KEY.format(sid=sid)
    count = await redis.incr(rl_key)
    if count == 1:
        await redis.expire(rl_key, _FRAME_RL_WIN)
    if count > _FRAME_RL_MAX:
        raise HTTPException(
            status_code=429,
            detail="Frame submission rate limit exceeded. Slow down capture interval.",
        )

    # Queue the analysis task
    from app.workers.stream_tasks import moderate_live_chunk_task

    moderate_live_chunk_task.delay(
        stream_id=sid,
        frames_b64=body.frames,
        transcript_hint=body.transcript_hint,
    )

    return MessageResponse(message="Frames queued for analysis.")


# ── GET /live/streams/{id}/alerts ─────────────────────────────────────────────


@router.get(
    "/streams/{stream_id}/alerts",
    response_model=AlertListResponse,
    summary="List moderation alerts for a stream",
)
async def list_stream_alerts(
    stream_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(50, ge=1, le=200),
    include_dismissed: bool = Query(False),
) -> AlertListResponse:
    q = select(Alert).where(Alert.stream_id == stream_id)
    if not include_dismissed:
        q = q.where(Alert.is_dismissed.is_(False))
    q = q.order_by(Alert.created_at.desc()).limit(limit)

    total_q = select(func.count()).select_from(
        select(Alert).where(Alert.stream_id == stream_id).subquery()
    )
    total_result = await db.execute(total_q)
    total = total_result.scalar_one()

    result = await db.execute(q)
    alerts = result.scalars().all()

    return AlertListResponse(
        items=[AlertResponse.model_validate(a) for a in alerts],
        total=total,
    )


# ── WS /live/ws/streams/{id} ──────────────────────────────────────────────────


@router.websocket("/ws/streams/{stream_id}")
async def websocket_stream(
    stream_id: str,
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> None:
    """
    WebSocket endpoint for real-time stream moderation events.

    Auth: JWT passed as ?token= query param.

    Events pushed to the client:
      { event: "frame.moderated",  violations: [...], face_analysis: {...}, ... }
      { event: "moderation.started", stream_id: "..." }
      { event: "moderation.stopped", stream_id: "..." }
      { event: "stream.stopped",    stream_id: "..." }

    The handler bridges Redis pub/sub channel "live:events:{stream_id}"
    to the WebSocket connection, so Celery workers can publish events
    without needing direct access to the WebSocket connection registry.
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
    channel = f"live:events:{stream_id}"
    logger.info("ws_client_connected", stream_id=stream_id, user=payload.get("sub"))

    # Create a dedicated Redis connection for pub/sub
    import redis.asyncio as aioredis

    pubsub_redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = pubsub_redis.pubsub()
    await pubsub.subscribe(channel)

    async def _forward_redis_to_ws() -> None:
        """Read events from Redis pub/sub and forward to the WebSocket."""
        async for message in pubsub.listen():
            if message["type"] == "message":
                with contextlib.suppress(Exception):
                    await websocket.send_text(message["data"])

    forward_task = asyncio.create_task(_forward_redis_to_ws())

    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        logger.info("ws_client_disconnected", stream_id=stream_id)
    finally:
        forward_task.cancel()
        with contextlib.suppress(Exception):
            await pubsub.unsubscribe(channel)
            await pubsub_redis.aclose()
