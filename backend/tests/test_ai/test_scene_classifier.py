"""Tests for A-05 SceneClassifierAgent — OpenAI mocked."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ai.agents.scene_classifier import SceneClassifierAgent
from app.ai.schemas import SceneCategory


@pytest.fixture()
def agent():
    return SceneClassifierAgent()


@pytest.fixture()
def mock_openai_response():
    """Build a fake OpenAI chat completion response."""

    def _make(payload: dict):
        msg = MagicMock()
        msg.content = json.dumps(payload)
        choice = MagicMock()
        choice.message = msg
        resp = MagicMock()
        resp.choices = [choice]
        return resp

    return _make


@pytest.mark.asyncio
async def test_no_frames_returns_empty(agent):
    result = await agent.run({"video_id": "v1", "frames": [], "frame_timestamps": []})
    assert result["scene_classifications"] == []
    assert "scene_classifier" in result["completed_agents"]


@pytest.mark.asyncio
async def test_classifies_single_frame(agent, mock_openai_response):
    payload = {"category": "safe", "confidence": 0.98, "sub_categories": []}
    fake_resp = mock_openai_response(payload)

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=fake_resp)
    agent._client = mock_client
    result = await agent.run(
        {
            "video_id": "v1",
            "frames": ["abc123"],
            "frame_timestamps": [0.0],
        }
    )

    classifications = result["scene_classifications"]
    assert len(classifications) == 1
    assert classifications[0]["category"] == SceneCategory.SAFE.value
    assert classifications[0]["confidence"] == 0.98


@pytest.mark.asyncio
async def test_classifies_multiple_frames(agent, mock_openai_response):
    payload = {"category": "violence", "confidence": 0.7, "sub_categories": ["fight"]}
    fake_resp = mock_openai_response(payload)

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=fake_resp)
    agent._client = mock_client
    result = await agent.run(
        {
            "video_id": "v2",
            "frames": ["f1", "f2", "f3"],
            "frame_timestamps": [0.0, 5.0, 10.0],
        }
    )

    assert len(result["scene_classifications"]) == 3
    for sc in result["scene_classifications"]:
        assert sc["category"] == "violence"


@pytest.mark.asyncio
async def test_api_error_adds_to_errors(agent):
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API unavailable"))
    agent._client = mock_client
    result = await agent.run(
        {
            "video_id": "v3",
            "frames": ["frame1"],
            "frame_timestamps": [0.0],
        }
    )

    # Frame fails gracefully — no classifications, error recorded
    assert result["scene_classifications"] == []
    assert any("API unavailable" in e for e in result.get("errors", []))
