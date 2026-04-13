"""
C-05 Moderation Workflow Graph

A lightweight LangGraph StateGraph focused exclusively on moderation decision-making.
Designed for fast-path scenarios where frame/audio extraction has already been done:
  - Live stream segment re-evaluation
  - Re-moderation of previously-processed videos
  - Quick policy re-check after rule changes

Workflow:
    load_context
         │
    run_moderation   ← calls moderation_chain (C-01)
         │
    evaluate_confidence
         │
    ┌────┴────────────────┐
    ▼ (low confidence)    ▼ (high confidence)
  escalate           finalize
    │                    │
    └──────┬─────────────┘
           ▼
       finalize  (always terminates here)

Public API:
    result = await run_moderation_workflow(
        video_id="...",
        content_summary="...",
        violations=[...],
        policy_rules=[...],
        scene_summary={...},
        transcript_excerpt="...",
        confidence_threshold=0.6,
    )
    result.decision            # ModerationDecision
    result.escalated           # bool
    result.recommended_action  # str
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, Literal, TypedDict

import structlog
from langgraph.graph import END, StateGraph
from pydantic import BaseModel

from app.ai.chains.moderation_chain import (
    ModerationChainOutput,
    run_moderation_chain,
)
from app.ai.schemas import ModerationDecision, ViolationSeverity

logger = structlog.get_logger(__name__)

_DEFAULT_CONFIDENCE_THRESHOLD = 0.6

# ── State ─────────────────────────────────────────────────────────────────────


class ModerationWorkflowState(TypedDict, total=False):
    # ── Input ─────────────────────────────────────────────────────────────────
    video_id: str
    content_summary: str
    violations: list[dict[str, Any]]
    policy_rules: list[dict[str, Any]]
    scene_summary: dict[str, int]
    transcript_excerpt: str
    confidence_threshold: float

    # ── Chain output ──────────────────────────────────────────────────────────
    chain_output: dict[str, Any]  # ModerationChainOutput.model_dump()

    # ── Workflow control ──────────────────────────────────────────────────────
    escalated: bool
    final_decision: str  # ModerationDecision value
    final_severity: str  # ViolationSeverity value
    final_confidence: float
    final_reasoning: str
    final_recommended_action: str

    # ── Accumulating lists (operator.add reducer for parallel safety) ─────────
    errors: Annotated[list[str], operator.add]


# ── Output schema ─────────────────────────────────────────────────────────────


class ModerationWorkflowResult(BaseModel):
    video_id: str
    decision: ModerationDecision
    overall_severity: ViolationSeverity
    confidence: float
    escalated: bool
    reasoning: str
    recommended_action: str
    errors: list[str] = []


# ── Injectable chain (allows test mocking) ────────────────────────────────────

_chain_fn = run_moderation_chain  # can be replaced in tests


# ── Node functions ────────────────────────────────────────────────────────────


async def load_context_node(state: ModerationWorkflowState) -> dict[str, Any]:
    """Validate required fields and set defaults."""
    errors: list[str] = []

    if not state.get("video_id"):
        errors.append("[load_context] video_id is required")
    if not state.get("content_summary"):
        logger.warning("moderation_workflow_no_summary", video_id=state.get("video_id"))

    return {
        "confidence_threshold": state.get("confidence_threshold", _DEFAULT_CONFIDENCE_THRESHOLD),
        "escalated": False,
        "errors": errors,
    }


async def run_moderation_node(state: ModerationWorkflowState) -> dict[str, Any]:
    """Call the moderation chain and store the raw output."""
    video_id = state.get("video_id", "")
    logger.info("moderation_workflow_chain_start", video_id=video_id)

    try:
        output: ModerationChainOutput = await _chain_fn(
            content_summary=state.get("content_summary", ""),
            violations=state.get("violations") or [],
            policy_rules=state.get("policy_rules") or [],
            scene_summary=state.get("scene_summary") or {},
            transcript_excerpt=state.get("transcript_excerpt", ""),
        )
        return {"chain_output": output.model_dump()}
    except Exception as exc:
        logger.error("moderation_workflow_chain_error", video_id=video_id, error=str(exc))
        fallback = ModerationChainOutput(
            decision=ModerationDecision.NEEDS_REVIEW,
            reasoning=f"Chain call failed: {exc}",
            recommended_action="escalate_to_human",
        )
        return {
            "chain_output": fallback.model_dump(),
            "errors": [f"[run_moderation] {exc}"],
        }


async def evaluate_confidence_node(state: ModerationWorkflowState) -> dict[str, Any]:
    """Check whether the chain output meets the confidence threshold."""
    chain_out = state.get("chain_output") or {}
    confidence = float(chain_out.get("confidence", 0.0))
    threshold = float(state.get("confidence_threshold", _DEFAULT_CONFIDENCE_THRESHOLD))

    should_escalate = confidence < threshold

    logger.info(
        "moderation_workflow_confidence_check",
        video_id=state.get("video_id"),
        confidence=confidence,
        threshold=threshold,
        escalating=should_escalate,
    )

    return {"escalated": should_escalate}


def _route_after_confidence(
    state: ModerationWorkflowState,
) -> Literal["escalate", "finalize"]:
    """Conditional edge: low confidence → escalate; high confidence → finalize."""
    return "escalate" if state.get("escalated") else "finalize"


async def escalate_node(state: ModerationWorkflowState) -> dict[str, Any]:
    """Override decision to ESCALATED when confidence is too low."""
    chain_out = state.get("chain_output") or {}
    logger.info(
        "moderation_workflow_escalating",
        video_id=state.get("video_id"),
        original_decision=chain_out.get("decision"),
    )
    return {
        "final_decision": ModerationDecision.ESCALATED.value,
        "final_severity": chain_out.get("overall_severity", ViolationSeverity.LOW.value),
        "final_confidence": float(chain_out.get("confidence", 0.0)),
        "final_reasoning": (
            f"Escalated due to low confidence ({chain_out.get('confidence', 0):.2f} "
            f"< threshold {state.get('confidence_threshold', _DEFAULT_CONFIDENCE_THRESHOLD):.2f}). "
            f"Original reasoning: {chain_out.get('reasoning', '')}"
        ),
        "final_recommended_action": "escalate_to_human",
    }


async def finalize_node(state: ModerationWorkflowState) -> dict[str, Any]:
    """Accept the chain decision as-is (only reached on the high-confidence path)."""
    chain_out = state.get("chain_output") or {}

    return {
        "final_decision": chain_out.get("decision", ModerationDecision.NEEDS_REVIEW.value),
        "final_severity": chain_out.get("overall_severity", ViolationSeverity.LOW.value),
        "final_confidence": float(chain_out.get("confidence", 0.5)),
        "final_reasoning": chain_out.get("reasoning", ""),
        "final_recommended_action": chain_out.get("recommended_action", "flag_for_review"),
    }


# ── Build graph ───────────────────────────────────────────────────────────────


def _build_workflow() -> Any:
    graph = StateGraph(ModerationWorkflowState)

    graph.add_node("load_context", load_context_node)
    graph.add_node("run_moderation", run_moderation_node)
    graph.add_node("evaluate_confidence", evaluate_confidence_node)
    graph.add_node("escalate", escalate_node)
    graph.add_node("finalize", finalize_node)

    graph.set_entry_point("load_context")
    graph.add_edge("load_context", "run_moderation")
    graph.add_edge("run_moderation", "evaluate_confidence")
    graph.add_conditional_edges(
        "evaluate_confidence",
        _route_after_confidence,
        {"escalate": "escalate", "finalize": "finalize"},
    )
    graph.add_edge("escalate", END)
    graph.add_edge("finalize", END)

    return graph.compile()


_compiled_workflow = _build_workflow()


# ── Public API ────────────────────────────────────────────────────────────────


async def run_moderation_workflow(
    video_id: str,
    content_summary: str = "",
    violations: list[dict[str, Any]] | None = None,
    policy_rules: list[dict[str, Any]] | None = None,
    scene_summary: dict[str, int] | None = None,
    transcript_excerpt: str = "",
    confidence_threshold: float = _DEFAULT_CONFIDENCE_THRESHOLD,
) -> ModerationWorkflowResult:
    """
    Run the fast moderation workflow for an already-processed video.

    Args:
        video_id:             UUID string of the video being evaluated.
        content_summary:      Short description of the video content.
        violations:           Pre-detected violations (can be empty).
        policy_rules:         Active policy rules to enforce.
        scene_summary:        Scene category → frame count.
        transcript_excerpt:   Relevant portion of the transcript.
        confidence_threshold: Minimum confidence to accept a decision without escalation.

    Returns:
        ModerationWorkflowResult — final decision with escalation flag.
    """
    initial: ModerationWorkflowState = {
        "video_id": video_id,
        "content_summary": content_summary,
        "violations": violations or [],
        "policy_rules": policy_rules or [],
        "scene_summary": scene_summary or {},
        "transcript_excerpt": transcript_excerpt,
        "confidence_threshold": confidence_threshold,
        "errors": [],
    }

    logger.info("moderation_workflow_start", video_id=video_id)

    try:
        final: ModerationWorkflowState = await _compiled_workflow.ainvoke(initial)
    except Exception as exc:
        logger.error("moderation_workflow_fatal", video_id=video_id, error=str(exc))
        return ModerationWorkflowResult(
            video_id=video_id,
            decision=ModerationDecision.NEEDS_REVIEW,
            overall_severity=ViolationSeverity.LOW,
            confidence=0.0,
            escalated=True,
            reasoning=f"Workflow failed: {exc}",
            recommended_action="escalate_to_human",
            errors=[str(exc)],
        )

    logger.info(
        "moderation_workflow_done",
        video_id=video_id,
        decision=final.get("final_decision"),
        escalated=final.get("escalated"),
    )

    return ModerationWorkflowResult(
        video_id=video_id,
        decision=ModerationDecision(
            final.get("final_decision", ModerationDecision.NEEDS_REVIEW.value)
        ),
        overall_severity=ViolationSeverity(
            final.get("final_severity", ViolationSeverity.LOW.value)
        ),
        confidence=float(final.get("final_confidence", 0.0)),
        escalated=bool(final.get("escalated", False)),
        reasoning=final.get("final_reasoning", ""),
        recommended_action=final.get("final_recommended_action", "flag_for_review"),
        errors=list(final.get("errors") or []),
    )
