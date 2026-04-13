"""Tests for D-06 LiveStream and Alert models."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from app.models.alert import Alert, AlertSeverity, LiveStream, StreamStatus
from app.models.user import User


def _make_user(db_session):
    u = User(email=f"u{uuid.uuid4()}@test.ai", password_hash="hash")
    db_session.add(u)
    return u


class TestLiveStreamModel:
    @pytest.mark.asyncio
    async def test_create_stream_with_defaults(self, db_session):
        owner = _make_user(db_session)
        await db_session.flush()

        stream = LiveStream(title="Test Stream", owner_id=owner.id)
        db_session.add(stream)
        await db_session.flush()

        result = await db_session.execute(select(LiveStream).where(LiveStream.id == stream.id))
        s = result.scalar_one()

        assert s.status == StreamStatus.PENDING
        assert s.stopped_at is None
        assert s.ingest_url is None

    @pytest.mark.asyncio
    async def test_stream_status_active(self, db_session):
        owner = _make_user(db_session)
        await db_session.flush()

        stream = LiveStream(
            title="Active Stream",
            owner_id=owner.id,
            status=StreamStatus.ACTIVE,
            ingest_url="rtmp://ingest.vidshield.ai/live/abc",
        )
        db_session.add(stream)
        await db_session.flush()

        result = await db_session.execute(select(LiveStream).where(LiveStream.id == stream.id))
        s = result.scalar_one()
        assert s.status == StreamStatus.ACTIVE
        assert "rtmp://" in s.ingest_url

    @pytest.mark.asyncio
    async def test_stream_stopped_at_field(self, db_session):
        owner = _make_user(db_session)
        await db_session.flush()

        stream = LiveStream(
            title="Stopped Stream",
            owner_id=owner.id,
            status=StreamStatus.STOPPED,
            stopped_at="2024-01-01T10:00:00Z",
        )
        db_session.add(stream)
        await db_session.flush()

        result = await db_session.execute(select(LiveStream).where(LiveStream.id == stream.id))
        s = result.scalar_one()
        assert s.stopped_at == "2024-01-01T10:00:00Z"


class TestAlertModel:
    @pytest.mark.asyncio
    async def test_create_alert_with_defaults(self, db_session):
        owner = _make_user(db_session)
        await db_session.flush()

        stream = LiveStream(title=f"s{uuid.uuid4()}", owner_id=owner.id)
        db_session.add(stream)
        await db_session.flush()

        alert = Alert(stream_id=stream.id, message="Violence detected in frame.")
        db_session.add(alert)
        await db_session.flush()

        result = await db_session.execute(select(Alert).where(Alert.stream_id == stream.id))
        a = result.scalar_one()

        assert a.severity == AlertSeverity.MEDIUM
        assert a.is_dismissed is False
        assert a.message == "Violence detected in frame."

    @pytest.mark.asyncio
    async def test_alert_severity_enum(self, db_session):
        owner = _make_user(db_session)
        await db_session.flush()

        stream = LiveStream(title=f"s{uuid.uuid4()}", owner_id=owner.id)
        db_session.add(stream)
        await db_session.flush()

        for severity in AlertSeverity:
            alert = Alert(
                stream_id=stream.id,
                message=f"{severity.value} alert",
                severity=severity,
            )
            db_session.add(alert)

        await db_session.flush()

        result = await db_session.execute(select(Alert).where(Alert.stream_id == stream.id))
        alerts = result.scalars().all()
        assert len(alerts) == len(AlertSeverity)

    @pytest.mark.asyncio
    async def test_alert_dismiss(self, db_session):
        owner = _make_user(db_session)
        await db_session.flush()

        stream = LiveStream(title=f"s{uuid.uuid4()}", owner_id=owner.id)
        db_session.add(stream)
        await db_session.flush()

        alert = Alert(
            stream_id=stream.id,
            message="Test alert",
            is_dismissed=True,
            category="violence",
        )
        db_session.add(alert)
        await db_session.flush()

        result = await db_session.execute(select(Alert).where(Alert.id == alert.id))
        a = result.scalar_one()
        assert a.is_dismissed is True
        assert a.category == "violence"
