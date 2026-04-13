"""
C-01 Moderation Chain

LangChain LCEL chain that performs the core LLM-based moderation reasoning step:
given content context, detected violations, and active policy rules, it returns a
structured moderation decision with confidence and recommended action.

This chain is the reusable LLM-reasoning building block used by:
  - SafetyCheckerAgent (inline logic extracted here for reuse)
  - ModerationWorkflowGraph (C-05)
  - Any future worker or service needing a quick moderation call

Hard-stop rules (high-confidence nudity, zero-tolerance policies) remain in
SafetyCheckerAgent — this chain handles only the LLM reasoning step.

Public API:
    result = await run_moderation_chain(
        content_summary="...",
        violations=[{"category": "violence", "confidence": 0.8, ...}],
        policy_rules=[{"category": "violence", "threshold": 0.7, "name": "no_violence"}],
        scene_summary={"safe": 8, "violence": 2},
        transcript_excerpt="...",
    )
    result.decision             # "approved" | "rejected" | "escalated" | "needs_review"
    result.overall_severity     # "low" | "medium" | "high" | "critical"
    result.confidence           # float 0.0–1.0
    result.reasoning            # str
    result.recommended_action   # str
"""

from __future__ import annotations

import json
from typing import Any

import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.ai.schemas import ModerationDecision, ViolationSeverity
from app.config import settings

logger = structlog.get_logger(__name__)

_MODEL = "gpt-4o"

# ── Output schema ─────────────────────────────────────────────────────────────


class ModerationChainOutput(BaseModel):
    decision: ModerationDecision = ModerationDecision.NEEDS_REVIEW
    overall_severity: ViolationSeverity = ViolationSeverity.LOW
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    reasoning: str = ""
    recommended_action: str = Field(
        default="review",
        description=(
            "One of: approve, reject, escalate_to_human, flag_for_review, "
            "age_restrict, add_warning_label"
        ),
    )


# ── Prompts ───────────────────────────────────────────────────────────────────

_SYSTEM = """\
You are an AI content moderation decision engine. Given:
- A content summary of the video
- Detected violations (if any)
- Active policy rules
- Scene classification breakdown
- A transcript excerpt

Produce a structured moderation decision.

Return a JSON object:
{
  "decision": "approved" | "rejected" | "escalated" | "needs_review",
  "overall_severity": "low" | "medium" | "high" | "critical",
  "confidence": <float 0.0-1.0>,
  "reasoning": "<concise explanation of the decision>",
  "recommended_action": "approve" | "reject" | "escalate_to_human" | "flag_for_review" | "age_restrict" | "add_warning_label"
}

Guidelines:
- "approved" with "approve" action: content is clearly safe and within policy.
- "rejected" with "reject" action: content clearly violates policy; high confidence.
- "escalated" with "escalate_to_human" action: policy violation suspected but unclear; needs human review.
- "needs_review" with "flag_for_review": borderline content; low confidence in either direction.
- Use "age_restrict" or "add_warning_label" when content is legal but may be inappropriate for some audiences.
- When uncertain, prefer "needs_review" over "rejected".

No markdown, no extra text.
"""

_USER_TEMPLATE = """\
Moderation request:

Content summary: {content_summary}

Active policy rules:
{policy_rules}

Detected violations:
{violations}

Scene breakdown (category → frame count):
{scene_summary}

Transcript excerpt: {transcript_excerpt}

Return only the JSON object.
"""


# ── Public API ────────────────────────────────────────────────────────────────


async def run_moderation_chain(
    content_summary: str = "",
    violations: list[dict[str, Any]] | None = None,
    policy_rules: list[dict[str, Any]] | None = None,
    scene_summary: dict[str, int] | None = None,
    transcript_excerpt: str = "",
    *,
    _llm: ChatOpenAI | None = None,
) -> ModerationChainOutput:
    """
    Run the LLM-based moderation reasoning chain.

    Args:
        content_summary:    Short description of the video content.
        violations:         List of detected violations (from SceneClassifier / SafetyChecker).
        policy_rules:       Active policy rules to evaluate against.
        scene_summary:      Scene category → frame count mapping.
        transcript_excerpt: Relevant portion of the transcript.
        _llm:               Override LLM for testing.

    Returns:
        ModerationChainOutput — decision, severity, confidence, reasoning, recommended_action.
    """
    llm = _llm or ChatOpenAI(
        model=_MODEL,
        openai_api_key=settings.OPENAI_API_KEY,
        temperature=0.1,  # low temperature for more deterministic decisions
    )

    violations_str = json.dumps(violations, indent=2) if violations else "No violations detected."
    policy_str = (
        json.dumps(policy_rules, indent=2) if policy_rules else "Default platform policies apply."
    )
    scene_str = json.dumps(scene_summary) if scene_summary else "{}"

    user_content = _USER_TEMPLATE.format(
        content_summary=content_summary or "(no summary available)",
        policy_rules=policy_str,
        violations=violations_str,
        scene_summary=scene_str,
        transcript_excerpt=(transcript_excerpt[:1000] if transcript_excerpt else "(none)"),
    )

    messages = [
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=user_content),
    ]

    logger.info(
        "moderation_chain_start",
        violation_count=len(violations) if violations else 0,
        policy_count=len(policy_rules) if policy_rules else 0,
    )

    try:
        response = await llm.ainvoke(messages)
        raw: str = response.content or "{}"
        data = json.loads(raw)

        result = ModerationChainOutput(
            decision=ModerationDecision(data.get("decision", "needs_review")),
            overall_severity=ViolationSeverity(data.get("overall_severity", "low")),
            confidence=float(data.get("confidence", 0.5)),
            reasoning=data.get("reasoning", ""),
            recommended_action=data.get("recommended_action", "flag_for_review"),
        )

        logger.info(
            "moderation_chain_done",
            decision=result.decision,
            severity=result.overall_severity,
            confidence=result.confidence,
        )
        return result

    except Exception as exc:
        logger.error("moderation_chain_error", error=str(exc))
        # On failure, default to needs_review — never auto-approve on error
        return ModerationChainOutput(
            decision=ModerationDecision.NEEDS_REVIEW,
            overall_severity=ViolationSeverity.LOW,
            confidence=0.0,
            reasoning=f"Moderation chain failed: {exc}",
            recommended_action="escalate_to_human",
        )
