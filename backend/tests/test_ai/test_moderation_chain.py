"""Tests for C-01 ModerationChain — LLM mocked via _llm injection."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ai.chains.moderation_chain import ModerationChainOutput, run_moderation_chain
from app.ai.schemas import ModerationDecision, ViolationSeverity


def _mock_llm(payload: dict) -> MagicMock:
    response = MagicMock()
    response.content = json.dumps(payload)
    llm = MagicMock()
    llm.ainvoke = AsyncMock(return_value=response)
    return llm


@pytest.mark.asyncio
async def test_moderation_chain_approved():
    payload = {
        "decision": "approved",
        "overall_severity": "low",
        "confidence": 0.96,
        "reasoning": "No policy violations found.",
        "recommended_action": "approve",
    }
    result = await run_moderation_chain(
        content_summary="Cooking tutorial about pasta.",
        violations=[],
        policy_rules=[],
        scene_summary={"safe": 10},
        transcript_excerpt="Today we make pasta.",
        _llm=_mock_llm(payload),
    )
    assert isinstance(result, ModerationChainOutput)
    assert result.decision == ModerationDecision.APPROVED
    assert result.overall_severity == ViolationSeverity.LOW
    assert result.confidence == 0.96
    assert result.recommended_action == "approve"


@pytest.mark.asyncio
async def test_moderation_chain_rejected_with_violations():
    payload = {
        "decision": "rejected",
        "overall_severity": "high",
        "confidence": 0.89,
        "reasoning": "Graphic violence detected in multiple frames.",
        "recommended_action": "reject",
    }
    violations = [
        {
            "category": "violence",
            "severity": "high",
            "timestamp": 5.0,
            "confidence": 0.89,
            "description": "Physical altercation",
        }
    ]
    result = await run_moderation_chain(
        content_summary="Street fight footage.",
        violations=violations,
        policy_rules=[{"category": "violence", "threshold": 0.5}],
        _llm=_mock_llm(payload),
    )
    assert result.decision == ModerationDecision.REJECTED
    assert result.overall_severity == ViolationSeverity.HIGH
    assert result.recommended_action == "reject"


@pytest.mark.asyncio
async def test_moderation_chain_escalated_borderline():
    payload = {
        "decision": "escalated",
        "overall_severity": "medium",
        "confidence": 0.55,
        "reasoning": "Ambiguous content; recommend human review.",
        "recommended_action": "escalate_to_human",
    }
    result = await run_moderation_chain(
        content_summary="Ambiguous content.",
        violations=[],
        policy_rules=[],
        _llm=_mock_llm(payload),
    )
    assert result.decision == ModerationDecision.ESCALATED
    assert result.recommended_action == "escalate_to_human"


@pytest.mark.asyncio
async def test_moderation_chain_age_restrict():
    payload = {
        "decision": "approved",
        "overall_severity": "medium",
        "confidence": 0.78,
        "reasoning": "Legal content but suitable only for mature audiences.",
        "recommended_action": "age_restrict",
    }
    result = await run_moderation_chain(
        content_summary="Mature drama content.",
        _llm=_mock_llm(payload),
    )
    assert result.recommended_action == "age_restrict"
    assert result.decision == ModerationDecision.APPROVED


@pytest.mark.asyncio
async def test_moderation_chain_llm_failure_defaults_to_needs_review():
    llm = MagicMock()
    llm.ainvoke = AsyncMock(side_effect=Exception("OpenAI 500"))

    result = await run_moderation_chain(
        content_summary="Test content.",
        _llm=llm,
    )
    assert result.decision == ModerationDecision.NEEDS_REVIEW
    assert result.confidence == 0.0
    assert result.recommended_action == "escalate_to_human"
    assert "failed" in result.reasoning.lower()


@pytest.mark.asyncio
async def test_moderation_chain_output_defaults():
    out = ModerationChainOutput()
    assert out.decision == ModerationDecision.NEEDS_REVIEW
    assert out.overall_severity == ViolationSeverity.LOW
    assert out.confidence == 0.5
