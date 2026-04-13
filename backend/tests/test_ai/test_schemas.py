"""Tests for AI schemas — validation and serialisation."""

import pytest
from pydantic import ValidationError

from app.ai.schemas import (
    ContentAnalysisResult,
    ModerationDecision,
    ModerationReport,
    SafetyResult,
    SceneCategory,
    SceneClassification,
    Violation,
    ViolationSeverity,
)


def test_violation_confidence_bounds():
    with pytest.raises(ValidationError):
        Violation(
            category=SceneCategory.VIOLENCE,
            severity=ViolationSeverity.HIGH,
            timestamp=1.0,
            confidence=1.5,  # > 1.0 — should fail
            description="test",
        )


def test_scene_classification_roundtrip():
    sc = SceneClassification(
        frame_index=0,
        timestamp=5.0,
        category=SceneCategory.SAFE,
        confidence=0.95,
        sub_categories=["outdoor"],
    )
    data = sc.model_dump()
    sc2 = SceneClassification.model_validate(data)
    assert sc2.category == SceneCategory.SAFE
    assert sc2.confidence == 0.95


def test_moderation_report_defaults():
    report = ModerationReport(
        video_id="abc123",
        decision=ModerationDecision.APPROVED,
        confidence=0.9,
    )
    assert report.violations == []
    assert report.processing_errors == []
    assert report.overall_severity == ViolationSeverity.LOW


def test_safety_result_defaults():
    result = SafetyResult(decision=ModerationDecision.NEEDS_REVIEW)
    assert result.violations == []
    assert result.policy_triggers == []


def test_content_analysis_result():
    r = ContentAnalysisResult(summary="Test video about cooking.")
    assert r.sentiment == "neutral"
    assert r.language == "en"
