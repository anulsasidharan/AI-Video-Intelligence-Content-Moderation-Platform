"""
A-03 Safety Checker Agent

Policy-aware content moderation. Takes the content analysis and scene
classifications produced by earlier agents, evaluates them against active
policy rules, and outputs a structured SafetyResult with violations and a
moderation decision.
"""

from __future__ import annotations

import json
from collections import Counter
from typing import Any

import structlog

from app.ai.base import BaseAgent
from app.ai.prompts.moderation_prompts import SAFETY_CHECK_SYSTEM, SAFETY_CHECK_USER
from app.ai.schemas import (
    ModerationDecision,
    SafetyResult,
    SceneCategory,
    Violation,
    ViolationSeverity,
)

logger = structlog.get_logger(__name__)

_MODEL = "gpt-4o"


class SafetyCheckerAgent(BaseAgent):
    name = "safety_checker"

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        video_id: str = state.get("video_id", "")
        content_analysis: dict = state.get("content_analysis") or {}
        scene_classifications: list[dict] = state.get("scene_classifications") or []
        policy_rules: list[dict] = state.get("policy_rules") or []
        transcript: str = state.get("transcript") or ""

        logger.info(
            "safety_checker_start",
            video_id=video_id,
            policy_count=len(policy_rules),
            scene_count=len(scene_classifications),
        )

        # Build scene summary for prompt
        scene_summary = self._build_scene_summary(scene_classifications)

        # Check for hard-stop categories before calling LLM
        hard_stop = self._check_hard_stops(scene_classifications, policy_rules)
        if hard_stop:
            logger.warning("safety_checker_hard_stop", video_id=video_id, reason=hard_stop)
            result = SafetyResult(
                decision=ModerationDecision.REJECTED,
                overall_severity=ViolationSeverity.CRITICAL,
                violations=[],
                policy_triggers=[hard_stop],
                confidence=1.0,
                reasoning=f"Automatic rejection: {hard_stop}",
            )
            return {
                "safety_result": result.model_dump(),
                "completed_agents": self._mark_completed(state),
            }

        try:
            result = await self._call_with_retry(
                self._check,
                content_analysis,
                transcript,
                scene_summary,
                policy_rules,
            )
            logger.info(
                "safety_checker_done",
                video_id=video_id,
                decision=result.decision,
                violations=len(result.violations),
            )
            return {
                "safety_result": result.model_dump(),
                "completed_agents": self._mark_completed(state),
            }
        except Exception as exc:
            logger.error("safety_checker_error", video_id=video_id, error=str(exc))
            # Default to needs_review on failure — never auto-approve on error
            fallback = SafetyResult(
                decision=ModerationDecision.NEEDS_REVIEW,
                reasoning=f"Safety check failed: {exc}",
            )
            return {
                "safety_result": fallback.model_dump(),
                "errors": self._append_error(state, str(exc)),
                "completed_agents": self._mark_completed(state),
            }

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _build_scene_summary(self, scenes: list[dict]) -> dict[str, int]:
        categories = [s.get("category", "safe") for s in scenes]
        return dict(Counter(categories))

    def _check_hard_stops(self, scenes: list[dict], policy_rules: list[dict]) -> str | None:
        """Return a reason string if content triggers a hard-stop rule, else None."""
        hard_stop_categories = {
            SceneCategory.NUDITY.value,
            SceneCategory.SELF_HARM.value,
        }
        # Check if any policy rule sets threshold=0 (zero-tolerance)
        zero_tolerance: set[str] = set()
        for rule in policy_rules:
            if rule.get("threshold", 1) == 0:
                zero_tolerance.add(rule.get("category", ""))

        for scene in scenes:
            cat = scene.get("category", "safe")
            conf = scene.get("confidence", 0.0)
            if cat in hard_stop_categories and conf >= 0.9:
                return f"High-confidence {cat} detected (conf={conf:.2f})"
            if cat in zero_tolerance and conf >= 0.5:
                return f"Zero-tolerance policy triggered for {cat}"
        return None

    async def _check(
        self,
        content_analysis: dict,
        transcript: str,
        scene_summary: dict[str, int],
        policy_rules: list[dict],
    ) -> SafetyResult:
        user_prompt = SAFETY_CHECK_USER.format(
            policy_rules=(
                json.dumps(policy_rules, indent=2)
                if policy_rules
                else "Default platform policies apply."
            ),
            content_summary=content_analysis.get("summary", "(no summary)"),
            transcript_excerpt=transcript[:1000] if transcript else "(no transcript)",
            frame_count=sum(scene_summary.values()),
            scene_summary=json.dumps(scene_summary),
        )

        response = await self.client.chat.completions.create(
            model=_MODEL,
            max_tokens=1024,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SAFETY_CHECK_SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
        )

        raw = self._extract_json(response.choices[0].message.content)
        data = json.loads(raw)

        violations = [
            Violation(
                category=v.get("category", "other"),
                severity=v.get("severity", "low"),
                timestamp=float(v.get("timestamp", 0.0)),
                confidence=float(v.get("confidence", 0.5)),
                description=v.get("description", ""),
                frame_index=v.get("frame_index"),
            )
            for v in data.get("violations", [])
        ]

        return SafetyResult(
            decision=ModerationDecision(data.get("decision", "needs_review")),
            overall_severity=ViolationSeverity(data.get("overall_severity", "low")),
            violations=violations,
            policy_triggers=data.get("policy_triggers", []),
            confidence=float(data.get("confidence", 0.5)),
            reasoning=data.get("reasoning", ""),
        )
