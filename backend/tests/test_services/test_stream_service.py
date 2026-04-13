"""Tests for S-07 StreamService — DB and Redis mocked."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import NotFoundError
from app.models.alert import StreamStatus

# ── Helpers ────────────────────────────────────────────────────────────────────

_STREAM_ID = uuid.uuid4()
_OWNER_ID = uuid.uuid4()


def _make_stream(stream_id=None, status=StreamStatus.ACTIVE):
    s = MagicMock()
    s.id = stream_id or _STREAM_ID
    s.title = "Test Stream"
    s.status = status
    s.ingest_url = f"rtmp://us-east-1.ingest.vidshield.ai/live/{_STREAM_ID}"
    s.owner_id = _OWNER_ID
    s.tenant_id = None
    s.stopped_at = None
    s.created_at = None
    return s


def _make_db(stream=None, total=0):
    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = stream
    result_mock.scalar_one.return_value = total
    result_mock.scalars.return_value.all.return_value = [stream] if stream else []
    db.execute = AsyncMock(return_value=result_mock)
    db.add = MagicMock()
    db.flush = AsyncMock()
    return db


def _make_redis():
    redis = AsyncMock()
    redis.publish = AsyncMock()
    return redis


# ── list_streams ───────────────────────────────────────────────────────────────


class TestListStreams:
    @pytest.mark.asyncio
    async def test_returns_stream_list(self):
        from app.services.stream_service import StreamService

        stream = _make_stream()
        db = _make_db(stream=stream, total=1)
        redis = _make_redis()

        mock_list_resp = MagicMock()
        mock_list_resp.total = 1
        with (
            patch("app.services.stream_service.StreamResponse") as MockResp,
            patch(
                "app.services.stream_service.StreamListResponse",
                return_value=mock_list_resp,
            ),
        ):
            MockResp.model_validate.return_value = MagicMock()
            service = StreamService(db=db, redis=redis)
            result = await service.list_streams()

        assert result.total == 1


# ── create_stream ──────────────────────────────────────────────────────────────


class TestCreateStream:
    @pytest.mark.asyncio
    async def test_creates_stream_with_ingest_url(self):
        from app.schemas.live import StreamCreate
        from app.services.stream_service import StreamService

        stream = _make_stream()
        db = _make_db()
        redis = _make_redis()

        body = MagicMock(spec=StreamCreate)
        body.title = "Live Test"

        with (
            patch("app.services.stream_service.LiveStream", return_value=stream),
            patch("app.services.stream_service.StreamResponse") as MockResp,
        ):
            MockResp.model_validate.return_value = MagicMock()
            service = StreamService(db=db, redis=redis)
            await service.create_stream(_OWNER_ID, None, body)

        db.add.assert_called_once()
        db.flush.assert_awaited_once()


# ── get_stream ─────────────────────────────────────────────────────────────────


class TestGetStream:
    @pytest.mark.asyncio
    async def test_returns_stream_when_found(self):
        from app.services.stream_service import StreamService

        stream = _make_stream()
        db = _make_db(stream=stream)
        redis = _make_redis()

        with patch("app.services.stream_service.StreamResponse") as MockResp:
            MockResp.model_validate.return_value = MagicMock()
            service = StreamService(db=db, redis=redis)
            await service.get_stream(_STREAM_ID)

    @pytest.mark.asyncio
    async def test_raises_not_found_when_missing(self):
        from app.services.stream_service import StreamService

        db = _make_db(stream=None)
        redis = _make_redis()

        service = StreamService(db=db, redis=redis)
        with pytest.raises(NotFoundError):
            await service.get_stream(uuid.uuid4())


# ── stop_stream ────────────────────────────────────────────────────────────────


class TestStopStream:
    @pytest.mark.asyncio
    async def test_sets_stopped_status_and_broadcasts(self):
        from app.services.stream_service import StreamService

        stream = _make_stream(status=StreamStatus.ACTIVE)
        db = _make_db(stream=stream)
        redis = _make_redis()

        service = StreamService(db=db, redis=redis)
        await service.stop_stream(_STREAM_ID)

        assert stream.status == StreamStatus.STOPPED
        assert stream.stopped_at is not None
        redis.publish.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_raises_not_found_when_missing(self):
        from app.services.stream_service import StreamService

        db = _make_db(stream=None)
        redis = _make_redis()

        service = StreamService(db=db, redis=redis)
        with pytest.raises(NotFoundError):
            await service.stop_stream(uuid.uuid4())


# ── broadcast_event ────────────────────────────────────────────────────────────


class TestBroadcastEvent:
    @pytest.mark.asyncio
    async def test_publishes_to_redis_channel(self):
        from app.services.stream_service import StreamService

        db = _make_db()
        redis = _make_redis()

        service = StreamService(db=db, redis=redis)
        await service.broadcast_event(_STREAM_ID, "frame.alert", {"score": 0.9})

        redis.publish.assert_awaited_once()
        call_args = redis.publish.await_args
        assert f"stream:{_STREAM_ID}:events" == call_args[0][0]
        assert "frame.alert" in call_args[0][1]


# ── subscribe_websocket ────────────────────────────────────────────────────────


class TestSubscribeWebsocket:
    @pytest.mark.asyncio
    async def test_closes_with_4001_on_invalid_token(self):
        from jose import JWTError

        from app.services.stream_service import StreamService

        db = _make_db()
        redis = _make_redis()
        ws = AsyncMock()
        ws.close = AsyncMock()

        with patch("app.services.stream_service.decode_token", side_effect=JWTError("bad")):
            service = StreamService(db=db, redis=redis)
            await service.subscribe_websocket("stream-id", ws, "bad_token")

        ws.close.assert_awaited_once_with(code=4001)

    @pytest.mark.asyncio
    async def test_closes_with_4001_on_wrong_token_type(self):
        from app.services.stream_service import StreamService

        db = _make_db()
        redis = _make_redis()
        ws = AsyncMock()
        ws.close = AsyncMock()

        with patch("app.services.stream_service.decode_token", return_value={"type": "refresh"}):
            service = StreamService(db=db, redis=redis)
            await service.subscribe_websocket("stream-id", ws, "refresh_token")

        ws.close.assert_awaited_once_with(code=4001)
