"""Tests for T-04 ObjectDetector — OpenAI client mocked."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ai.tools.object_detector import ObjectDetectionResult, detect_objects

# ── Helpers ───────────────────────────────────────────────────────────────────


def _mock_client(payload: dict | None = None, side_effect=None) -> MagicMock:
    msg = MagicMock()
    msg.content = json.dumps(payload) if payload is not None else "{}"
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]

    client = MagicMock()
    client.chat.completions.create = AsyncMock(return_value=resp, side_effect=side_effect)
    return client


_FAKE_FRAME = "aGVsbG8="


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_detect_objects_happy_path():
    payload = {
        "objects": ["person", "car", "tree"],
        "frame_detections": [["person", "car"], ["tree"]],
    }
    result = await detect_objects([_FAKE_FRAME, _FAKE_FRAME], _client=_mock_client(payload))

    assert isinstance(result, ObjectDetectionResult)
    assert "person" in result.objects
    assert "car" in result.objects
    assert result.frame_detections == [["person", "car"], ["tree"]]
    assert result.error is None


@pytest.mark.asyncio
async def test_detect_objects_empty_frames_returns_empty():
    result = await detect_objects([], _client=_mock_client())
    assert result.objects == []
    assert result.frame_detections == []
    assert result.error is None


@pytest.mark.asyncio
async def test_detect_objects_api_failure_returns_error():
    client = _mock_client(side_effect=Exception("OpenAI timeout"))
    result = await detect_objects([_FAKE_FRAME], _client=client)

    assert result.objects == []
    assert "OpenAI timeout" in (result.error or "")


@pytest.mark.asyncio
async def test_detect_objects_max_frames_truncation():
    """Only max_frames frames should be sent to the API."""
    frames = [_FAKE_FRAME] * 15
    payload = {
        "objects": ["chair"],
        "frame_detections": [["chair"]] * 4,
    }
    client = _mock_client(payload)

    await detect_objects(frames, max_frames=4, _client=client)

    call_args = client.chat.completions.create.call_args
    user_content = call_args.kwargs["messages"][1]["content"]
    image_entries = [c for c in user_content if c.get("type") == "image_url"]
    assert len(image_entries) == 4


@pytest.mark.asyncio
async def test_detect_objects_single_frame():
    payload = {
        "objects": ["laptop", "desk"],
        "frame_detections": [["laptop", "desk"]],
    }
    result = await detect_objects([_FAKE_FRAME], _client=_mock_client(payload))

    assert "laptop" in result.objects
    assert len(result.frame_detections) == 1


@pytest.mark.asyncio
async def test_detect_objects_no_objects_found():
    payload = {"objects": [], "frame_detections": [[]]}
    result = await detect_objects([_FAKE_FRAME], _client=_mock_client(payload))

    assert result.objects == []
    assert result.error is None
