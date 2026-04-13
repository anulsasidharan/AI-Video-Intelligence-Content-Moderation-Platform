"""Tests for T-08 — summary_prompts.py template completeness."""

from app.ai.prompts.summary_prompts import (
    REPORT_SYSTEM,
    REPORT_USER,
    SUMMARY_SYSTEM,
    SUMMARY_USER,
)


class TestSummaryPrompts:
    def test_summary_system_not_empty(self):
        assert len(SUMMARY_SYSTEM.strip()) > 0

    def test_summary_system_requests_json(self):
        assert "JSON" in SUMMARY_SYSTEM

    def test_summary_system_includes_content_rating(self):
        assert "content_rating" in SUMMARY_SYSTEM

    def test_summary_user_has_required_placeholders(self):
        required = {"{content_summary}", "{topics}", "{duration}", "{transcript}"}
        for placeholder in required:
            assert placeholder in SUMMARY_USER, f"Missing placeholder: {placeholder}"

    def test_summary_user_renders_without_error(self):
        rendered = SUMMARY_USER.format(
            content_summary="A cooking video.",
            topics="cooking, pasta",
            duration="120s",
            transcript="Today we make pasta.",
        )
        assert "cooking" in rendered
        assert "pasta" in rendered

    def test_report_system_not_empty(self):
        assert len(REPORT_SYSTEM.strip()) > 0

    def test_report_user_has_required_placeholders(self):
        required = {
            "{content_analysis}",
            "{safety_result}",
            "{metadata}",
            "{scene_summary}",
        }
        for placeholder in required:
            assert placeholder in REPORT_USER, f"Missing placeholder: {placeholder}"

    def test_report_user_renders_without_error(self):
        rendered = REPORT_USER.format(
            content_analysis="{}",
            safety_result="{}",
            metadata="{}",
            scene_summary="{}",
        )
        assert len(rendered) > 0
