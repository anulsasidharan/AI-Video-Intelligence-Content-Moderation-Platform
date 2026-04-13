"""Tests for A-04 MetadataExtractorAgent — OpenAI mocked."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ai.agents.metadata_extractor import MetadataExtractorAgent


@pytest.fixture()
def agent():
    return MetadataExtractorAgent()


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
async def test_metadata_extraction_happy_path(agent):
    payload = {
        "entities": ["Gordon Ramsay", "BBC"],
        "brands": ["BBC"],
        "keywords": ["cooking", "chef"],
        "ocr_text": ["CHEF'S TABLE"],
        "objects_detected": ["knife", "pan"],
        "locations": ["London"],
    }
    agent._client = _mock_client(return_value=_fake_response(payload))
    result = await agent.run(
        {
            "video_id": "v1",
            "frames": ["frame_b64"],
            "transcript": "Gordon Ramsay cooks in London.",
        }
    )

    meta = result["metadata"]
    assert "Gordon Ramsay" in meta["entities"]
    assert "knife" in meta["objects_detected"]
    assert "metadata_extractor" in result["completed_agents"]


@pytest.mark.asyncio
async def test_metadata_extraction_empty_video(agent):
    payload = {
        "entities": [],
        "brands": [],
        "keywords": [],
        "ocr_text": [],
        "objects_detected": [],
        "locations": [],
    }
    agent._client = _mock_client(return_value=_fake_response(payload))
    result = await agent.run({"video_id": "v2", "frames": [], "transcript": ""})

    assert result["metadata"]["entities"] == []


@pytest.mark.asyncio
async def test_metadata_extraction_api_failure_returns_empty(agent):
    agent._client = _mock_client(side_effect=Exception("rate limited"))
    result = await agent.run({"video_id": "v3", "frames": ["f"], "transcript": "hi"})

    assert result["metadata"] == {
        "entities": [],
        "brands": [],
        "keywords": [],
        "ocr_text": [],
        "objects_detected": [],
        "locations": [],
    }
    assert any("rate limited" in e for e in result.get("errors", []))
