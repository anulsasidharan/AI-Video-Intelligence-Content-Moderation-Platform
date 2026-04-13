"""Tests for A-02 ContentAnalyzerAgent — OpenAI mocked."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ai.agents.content_analyzer import ContentAnalyzerAgent


@pytest.fixture()
def agent():
    return ContentAnalyzerAgent()


def _fake_response(payload: dict) -> MagicMock:
    msg = MagicMock()
    msg.content = json.dumps(payload)
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def _mock_client(return_value=None, side_effect=None) -> MagicMock:
    mc = MagicMock()
    mc.chat.completions.create = AsyncMock(return_value=return_value, side_effect=side_effect)
    return mc


@pytest.mark.asyncio
async def test_content_analysis_happy_path(agent):
    payload = {
        "summary": "A cooking tutorial about pasta.",
        "topics": ["cooking", "pasta"],
        "sentiment": "positive",
        "language": "en",
        "duration_seconds": 120.0,
    }
    agent._client = _mock_client(return_value=_fake_response(payload))
    result = await agent.run(
        {
            "video_id": "v1",
            "frames": ["abc"],
            "transcript": "Today we make pasta.",
        }
    )

    ca = result["content_analysis"]
    assert ca["summary"] == "A cooking tutorial about pasta."
    assert "cooking" in ca["topics"]
    assert ca["sentiment"] == "positive"
    assert "content_analyzer" in result["completed_agents"]


@pytest.mark.asyncio
async def test_content_analysis_no_frames(agent):
    payload = {
        "summary": "Audio-only content.",
        "topics": [],
        "sentiment": "neutral",
        "language": "en",
    }
    agent._client = _mock_client(return_value=_fake_response(payload))
    result = await agent.run(
        {
            "video_id": "v2",
            "frames": [],
            "transcript": "Hello everyone.",
        }
    )

    assert result["content_analysis"]["summary"] == "Audio-only content."


@pytest.mark.asyncio
async def test_content_analysis_api_failure_returns_fallback(agent):
    agent._client = _mock_client(side_effect=Exception("OpenAI timeout"))
    result = await agent.run({"video_id": "v3", "frames": ["f1"], "transcript": ""})

    ca = result["content_analysis"]
    assert "failed" in ca["summary"].lower()
    assert any("OpenAI timeout" in e for e in result.get("errors", []))
