"""
Tests for C-05 ModerationWorkflowGraph — moderation_chain mocked.

Injects a mock chain function directly into the graph module to avoid
real OpenAI calls while still testing the full LangGraph routing logic.
"""

from unittest.mock import AsyncMock

import pytest

import app.ai.graphs.moderation_workflow as wf_module
from app.ai.chains.moderation_chain import ModerationChainOutput
from app.ai.graphs.moderation_workflow import (
    ModerationWorkflowResult,
    run_moderation_workflow,
)
from app.ai.schemas import ModerationDecision, ViolationSeverity


def _mock_chain(output: ModerationChainOutput):
    """Replace the module-level _chain_fn with a mock returning the given output."""
    wf_module._chain_fn = AsyncMock(return_value=output)


def _restore_chain():
    """Restore the real chain function after each test."""
    from app.ai.chains.moderation_chain import run_moderation_chain

    wf_module._chain_fn = run_moderation_chain


@pytest.fixture(autouse=True)
def restore_chain_fn():
    yield
    _restore_chain()


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_workflow_approved_high_confidence():
    _mock_chain(
        ModerationChainOutput(
            decision=ModerationDecision.APPROVED,
            overall_severity=ViolationSeverity.LOW,
            confidence=0.95,
            reasoning="Clean content.",
            recommended_action="approve",
        )
    )

    result = await run_moderation_workflow(
        video_id="v001",
        content_summary="Cooking tutorial.",
        confidence_threshold=0.6,
    )

    assert isinstance(result, ModerationWorkflowResult)
    assert result.decision == ModerationDecision.APPROVED
    assert result.escalated is False
    assert result.recommended_action == "approve"
    assert result.confidence == 0.95


@pytest.mark.asyncio
async def test_workflow_rejected_high_confidence():
    _mock_chain(
        ModerationChainOutput(
            decision=ModerationDecision.REJECTED,
            overall_severity=ViolationSeverity.HIGH,
            confidence=0.91,
            reasoning="Graphic violence.",
            recommended_action="reject",
        )
    )

    result = await run_moderation_workflow(
        video_id="v002",
        content_summary="Street fight footage.",
        violations=[{"category": "violence", "confidence": 0.91}],
        confidence_threshold=0.6,
    )

    assert result.decision == ModerationDecision.REJECTED
    assert result.escalated is False
    assert result.recommended_action == "reject"


@pytest.mark.asyncio
async def test_workflow_escalates_on_low_confidence():
    """When chain confidence < threshold, workflow overrides decision to ESCALATED."""
    _mock_chain(
        ModerationChainOutput(
            decision=ModerationDecision.APPROVED,
            overall_severity=ViolationSeverity.LOW,
            confidence=0.45,  # below default threshold of 0.6
            reasoning="Uncertain.",
            recommended_action="approve",
        )
    )

    result = await run_moderation_workflow(
        video_id="v003",
        content_summary="Ambiguous content.",
        confidence_threshold=0.6,
    )

    assert result.decision == ModerationDecision.ESCALATED
    assert result.escalated is True
    assert result.recommended_action == "escalate_to_human"
    assert "low confidence" in result.reasoning.lower()


@pytest.mark.asyncio
async def test_workflow_custom_threshold():
    """A very high threshold forces escalation even on moderately confident decisions."""
    _mock_chain(
        ModerationChainOutput(
            decision=ModerationDecision.APPROVED,
            overall_severity=ViolationSeverity.LOW,
            confidence=0.75,
            reasoning="Likely safe.",
            recommended_action="approve",
        )
    )

    result = await run_moderation_workflow(
        video_id="v004",
        content_summary="Edge case content.",
        confidence_threshold=0.90,  # higher than chain output's 0.75
    )

    assert result.escalated is True
    assert result.decision == ModerationDecision.ESCALATED


@pytest.mark.asyncio
async def test_workflow_chain_failure_returns_safe_fallback():
    """
    If the chain throws, the fallback has confidence=0.0 which is below the
    default threshold (0.6), so the workflow escalates — never auto-approves on error.
    """
    wf_module._chain_fn = AsyncMock(side_effect=Exception("chain crashed"))

    result = await run_moderation_workflow(
        video_id="v005",
        content_summary="Test content.",
    )

    # Confidence 0.0 < threshold 0.6 → escalated by the confidence check node
    assert result.escalated is True
    assert result.recommended_action == "escalate_to_human"
    # Decision is ESCALATED (overridden by escalate_node) — safe default
    assert result.decision in (
        ModerationDecision.ESCALATED,
        ModerationDecision.NEEDS_REVIEW,
    )


@pytest.mark.asyncio
async def test_workflow_result_contains_video_id():
    _mock_chain(
        ModerationChainOutput(
            decision=ModerationDecision.APPROVED,
            confidence=0.9,
            recommended_action="approve",
        )
    )

    result = await run_moderation_workflow(video_id="my-video-123")
    assert result.video_id == "my-video-123"


@pytest.mark.asyncio
async def test_workflow_with_policy_rules_and_violations():
    _mock_chain(
        ModerationChainOutput(
            decision=ModerationDecision.REJECTED,
            overall_severity=ViolationSeverity.CRITICAL,
            confidence=0.98,
            reasoning="Zero-tolerance policy triggered.",
            recommended_action="reject",
        )
    )

    result = await run_moderation_workflow(
        video_id="v006",
        content_summary="Dangerous content.",
        violations=[{"category": "self_harm", "confidence": 0.98}],
        policy_rules=[{"category": "self_harm", "threshold": 0}],
        confidence_threshold=0.6,
    )

    assert result.decision == ModerationDecision.REJECTED
    assert result.escalated is False
    assert result.overall_severity == ViolationSeverity.CRITICAL
