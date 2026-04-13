"""Tests for A-03 SafetyCheckerAgent — OpenAI mocked."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ai.agents.safety_checker import SafetyCheckerAgent
from app.ai.schemas import ModerationDecision


@pytest.fixture()
def agent():
    return SafetyCheckerAgent()


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
async def test_safe_content_approved(agent):
    payload = {
        "decision": "approved",
        "overall_severity": "low",
        "confidence": 0.95,
        "reasoning": "No violations detected.",
        "violations": [],
        "policy_triggers": [],
    }
    agent._client = _mock_client(return_value=_fake_response(payload))
    result = await agent.run(
        {
            "video_id": "v1",
            "content_analysis": {"summary": "Cooking tutorial"},
            "scene_classifications": [{"category": "safe", "confidence": 0.99, "timestamp": 0.0}],
            "policy_rules": [],
            "transcript": "Making pasta today.",
        }
    )

    sr = result["safety_result"]
    assert sr["decision"] == ModerationDecision.APPROVED.value
    assert sr["violations"] == []


@pytest.mark.asyncio
async def test_violence_detected_rejected(agent):
    payload = {
        "decision": "rejected",
        "overall_severity": "high",
        "confidence": 0.87,
        "reasoning": "Violence detected in multiple frames.",
        "violations": [
            {
                "category": "violence",
                "severity": "high",
                "timestamp": 12.0,
                "confidence": 0.87,
                "description": "Physical altercation",
                "frame_index": 2,
            }
        ],
        "policy_triggers": ["no_violence"],
    }
    agent._client = _mock_client(return_value=_fake_response(payload))
    result = await agent.run(
        {
            "video_id": "v2",
            "content_analysis": {"summary": "Street fight footage"},
            "scene_classifications": [
                {"category": "violence", "confidence": 0.87, "timestamp": 12.0}
            ],
            "policy_rules": [{"category": "violence", "threshold": 0.5, "name": "no_violence"}],
            "transcript": "",
        }
    )

    sr = result["safety_result"]
    assert sr["decision"] == ModerationDecision.REJECTED.value
    assert len(sr["violations"]) == 1


@pytest.mark.asyncio
async def test_hard_stop_nudity_high_confidence(agent):
    """High-confidence nudity should trigger hard-stop without calling LLM."""
    result = await agent.run(
        {
            "video_id": "v3",
            "content_analysis": {},
            "scene_classifications": [{"category": "nudity", "confidence": 0.95, "timestamp": 5.0}],
            "policy_rules": [],
            "transcript": "",
        }
    )

    sr = result["safety_result"]
    assert sr["decision"] == ModerationDecision.REJECTED.value
    assert sr["overall_severity"] == "critical"
    assert "nudity" in sr["policy_triggers"][0]


@pytest.mark.asyncio
async def test_api_failure_defaults_to_needs_review(agent):
    agent._client = _mock_client(side_effect=Exception("network error"))
    result = await agent.run(
        {
            "video_id": "v4",
            "content_analysis": {"summary": "unknown"},
            "scene_classifications": [{"category": "safe", "confidence": 0.5}],
            "policy_rules": [],
            "transcript": "",
        }
    )

    sr = result["safety_result"]
    assert sr["decision"] == ModerationDecision.NEEDS_REVIEW.value


@pytest.mark.asyncio
async def test_zero_tolerance_policy_triggers_hard_stop(agent):
    result = await agent.run(
        {
            "video_id": "v5",
            "content_analysis": {},
            "scene_classifications": [{"category": "drugs", "confidence": 0.6, "timestamp": 3.0}],
            "policy_rules": [{"category": "drugs", "threshold": 0}],
            "transcript": "",
        }
    )

    sr = result["safety_result"]
    assert sr["decision"] == ModerationDecision.REJECTED.value
