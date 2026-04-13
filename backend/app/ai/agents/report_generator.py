"""
A-06 Report Generator Agent

Synthesises outputs from ContentAnalyzer, SafetyChecker, MetadataExtractor,
and SceneClassifier into a final ModerationReport that is persisted to the DB.
"""

from __future__ import annotations

import json
from collections import Counter
from typing import Any

import structlog

from app.ai.base import BaseAgent
from app.ai.prompts.summary_prompts import REPORT_SYSTEM, REPORT_USER
from app.ai.schemas import (
    ModerationDecision,
    ModerationReport,
    Violation,
    ViolationSeverity,
)

logger = structlog.get_logger(__name__)

_MODEL = "gpt-4o-mini"  # cheaper — report synthesis doesn't need full 4o


class ReportGeneratorAgent(BaseAgent):
    name = "report_generator"

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        video_id: str = state.get("video_id", "")
        content_analysis: dict = state.get("content_analysis") or {}
        safety_result: dict = state.get("safety_result") or {}
        metadata: dict = state.get("metadata") or {}
        scene_classifications: list[dict] = state.get("scene_classifications") or []

        logger.info("report_generator_start", video_id=video_id)

        scene_summary = dict(Counter(s.get("category", "safe") for s in scene_classifications))

        try:
            report = await self._call_with_retry(
                self._generate,
                video_id,
                content_analysis,
                safety_result,
                metadata,
                scene_summary,
                state,
            )
            logger.info(
                "report_generator_done",
                video_id=video_id,
                decision=report.decision,
            )
            return {
                "moderation_report": report.model_dump(),
                "completed_agents": self._mark_completed(state),
            }
        except Exception as exc:
            logger.error("report_generator_error", video_id=video_id, error=str(exc))
            # Fall back to a minimal report derived from safety_result
            fallback = self._fallback_report(video_id, safety_result, state, str(exc))
            return {
                "moderation_report": fallback.model_dump(),
                "errors": self._append_error(state, str(exc)),
                "completed_agents": self._mark_completed(state),
            }

    # ── Helpers ───────────────────────────────────────────────────────────────

    async def _generate(
        self,
        video_id: str,
        content_analysis: dict,
        safety_result: dict,
        metadata: dict,
        scene_summary: dict[str, int],
        state: dict[str, Any],
    ) -> ModerationReport:
        user_prompt = REPORT_USER.format(
            content_analysis=json.dumps(content_analysis, indent=2),
            safety_result=json.dumps(safety_result, indent=2),
            metadata=json.dumps(metadata, indent=2),
            scene_summary=json.dumps(scene_summary, indent=2),
        )

        response = await self.client.chat.completions.create(
            model=_MODEL,
            max_tokens=512,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": REPORT_SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
        )

        raw = self._extract_json(response.choices[0].message.content)
        data = json.loads(raw)

        violations = [Violation(**v) for v in safety_result.get("violations", [])]

        return ModerationReport(
            video_id=video_id,
            decision=ModerationDecision(data.get("decision", "needs_review")),
            overall_severity=ViolationSeverity(data.get("overall_severity", "low")),
            confidence=float(data.get("confidence", 0.5)),
            violations=violations,
            content_summary=data.get("content_summary", content_analysis.get("summary", "")),
            reasoning=safety_result.get("reasoning", ""),
            metadata=metadata,
            scene_summary=scene_summary,
            policy_triggers=safety_result.get("policy_triggers", data.get("policy_triggers", [])),
            transcript_excerpt=data.get("transcript_excerpt", ""),
            processing_errors=[],
            agents_completed=[],
        )

    def _fallback_report(
        self,
        video_id: str,
        safety_result: dict,
        state: dict[str, Any],
        error: str,
    ) -> ModerationReport:
        violations = [Violation(**v) for v in safety_result.get("violations", [])]
        return ModerationReport(
            video_id=video_id,
            decision=ModerationDecision(safety_result.get("decision", "needs_review")),
            overall_severity=ViolationSeverity(safety_result.get("overall_severity", "low")),
            confidence=float(safety_result.get("confidence", 0.5)),
            violations=violations,
            content_summary="Report generation failed; derived from safety result.",
            policy_triggers=safety_result.get("policy_triggers", []),
            processing_errors=[error],
            agents_completed=[],
        )
