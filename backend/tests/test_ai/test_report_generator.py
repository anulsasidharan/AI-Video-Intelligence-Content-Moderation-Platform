"""Tests for A-06 ReportGeneratorAgent — OpenAI mocked."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ai.agents.report_generator import ReportGeneratorAgent
from app.ai.schemas import ModerationDecision


@pytest.fixture()
def agent():
    return ReportGeneratorAgent()


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


_CONTENT_ANALYSIS = {
    "summary": "Cooking tutorial.",
    "topics": ["cooking"],
    "sentiment": "positive",
    "language": "en",
}
_SAFETY_RESULT = {
    "decision": "approved",
    "overall_severity": "low",
    "confidence": 0.96,
    "violations": [],
    "policy_triggers": [],
    "reasoning": "Clean content.",
}
_METADATA = {
    "entities": [],
    "brands": [],
    "keywords": ["pasta"],
    "ocr_text": [],
    "objects_detected": [],
    "locations": [],
}


@pytest.mark.asyncio
async def test_report_generation_happy_path(agent):
    payload = {
        "decision": "approved",
        "overall_severity": "low",
        "confidence": 0.96,
        "content_summary": "Cooking tutorial about pasta.",
        "policy_triggers": [],
        "transcript_excerpt": "",
    }
    agent._client = _mock_client(return_value=_fake_response(payload))
    result = await agent.run(
        {
            "video_id": "v1",
            "content_analysis": _CONTENT_ANALYSIS,
            "safety_result": _SAFETY_RESULT,
            "metadata": _METADATA,
            "scene_classifications": [{"category": "safe", "confidence": 0.99}],
        }
    )

    report = result["moderation_report"]
    assert report["decision"] == ModerationDecision.APPROVED.value
    assert report["video_id"] == "v1"
    assert report["confidence"] > 0


@pytest.mark.asyncio
async def test_report_fallback_on_api_failure(agent):
    agent._client = _mock_client(side_effect=Exception("service down"))
    result = await agent.run(
        {
            "video_id": "v2",
            "content_analysis": _CONTENT_ANALYSIS,
            "safety_result": _SAFETY_RESULT,
            "metadata": _METADATA,
            "scene_classifications": [],
        }
    )

    # Fallback derives decision from safety_result
    report = result["moderation_report"]
    assert report["decision"] == ModerationDecision.APPROVED.value
    assert any("service down" in e for e in report["processing_errors"])


@pytest.mark.asyncio
async def test_report_includes_violations_from_safety(agent):
    safety_with_violations = {
        **_SAFETY_RESULT,
        "decision": "rejected",
        "overall_severity": "high",
        "violations": [
            {
                "category": "violence",
                "severity": "high",
                "timestamp": 5.0,
                "confidence": 0.85,
                "description": "Fight scene",
                "frame_index": 1,
            }
        ],
    }
    payload = {
        "decision": "rejected",
        "overall_severity": "high",
        "confidence": 0.85,
        "content_summary": "Video with violence.",
        "policy_triggers": ["no_violence"],
        "transcript_excerpt": "",
    }
    agent._client = _mock_client(return_value=_fake_response(payload))
    result = await agent.run(
        {
            "video_id": "v3",
            "content_analysis": _CONTENT_ANALYSIS,
            "safety_result": safety_with_violations,
            "metadata": _METADATA,
            "scene_classifications": [],
        }
    )

    report = result["moderation_report"]
    assert report["decision"] == "rejected"
    assert len(report["violations"]) == 1
    assert report["violations"][0]["category"] == "violence"
