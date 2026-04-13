"""Tests for T-03 OCRTool — OpenAI client mocked."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ai.tools.ocr_tool import OCRResult, run_ocr

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


_FAKE_FRAME = "aGVsbG8="  # base64("hello")


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ocr_happy_path():
    payload = {
        "texts": ["SALE 50%", ""],
        "combined_text": "SALE 50%",
    }
    result = await run_ocr([_FAKE_FRAME, _FAKE_FRAME], _client=_mock_client(payload))

    assert isinstance(result, OCRResult)
    assert result.texts == ["SALE 50%", ""]
    assert result.combined_text == "SALE 50%"
    assert result.error is None


@pytest.mark.asyncio
async def test_ocr_empty_frames_returns_empty():
    result = await run_ocr([], _client=_mock_client())
    assert result.texts == []
    assert result.combined_text == ""
    assert result.error is None


@pytest.mark.asyncio
async def test_ocr_api_failure_returns_error():
    client = _mock_client(side_effect=Exception("OpenAI 429"))
    result = await run_ocr([_FAKE_FRAME], _client=client)

    assert result.texts == []
    assert "OpenAI 429" in (result.error or "")


@pytest.mark.asyncio
async def test_ocr_max_frames_truncation():
    """Only max_frames frames are sent to the API."""
    frames = [_FAKE_FRAME] * 20
    payload = {"texts": ["text"] * 5, "combined_text": "text text text text text"}
    client = _mock_client(payload)

    await run_ocr(frames, max_frames=5, _client=client)

    call_args = client.chat.completions.create.call_args
    user_content = call_args.kwargs["messages"][1]["content"]
    image_entries = [c for c in user_content if c.get("type") == "image_url"]
    assert len(image_entries) == 5


@pytest.mark.asyncio
async def test_ocr_no_text_in_frames():
    payload = {"texts": ["", ""], "combined_text": ""}
    result = await run_ocr([_FAKE_FRAME, _FAKE_FRAME], _client=_mock_client(payload))

    assert result.texts == ["", ""]
    assert result.combined_text == ""
    assert result.error is None


@pytest.mark.asyncio
async def test_ocr_single_frame():
    payload = {"texts": ["WARNING"], "combined_text": "WARNING"}
    result = await run_ocr([_FAKE_FRAME], _client=_mock_client(payload))

    assert result.texts == ["WARNING"]
    assert result.combined_text == "WARNING"
