"""
LangGraph StateGraph — Video Analysis Pipeline

Node execution order:
  orchestrator
      │
      ├── content_analyzer  ─┐
      ├── scene_classifier   ├─► safety_checker ──► report_generator
      └── metadata_extractor ┘

Content analyzer, scene classifier, and metadata extractor run in parallel
(LangGraph fan-out). Safety checker waits for all three, then report
generator runs last.
"""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from langgraph.graph import END, StateGraph

from app.ai.agents.content_analyzer import ContentAnalyzerAgent
from app.ai.agents.metadata_extractor import MetadataExtractorAgent
from app.ai.agents.orchestrator import OrchestratorAgent
from app.ai.agents.report_generator import ReportGeneratorAgent
from app.ai.agents.safety_checker import SafetyCheckerAgent
from app.ai.agents.scene_classifier import SceneClassifierAgent
from app.ai.pipeline_agent_audit import (
    record_pipeline_audit_sync,
    run_audited_pipeline_step,
)
from app.ai.schemas import ModerationReport
from app.ai.state import VideoAnalysisState
from app.models.agent_audit import AgentAuditStatus

logger = structlog.get_logger(__name__)

# ── Instantiate agents (singletons — shared across requests) ─────────────────

_orchestrator = OrchestratorAgent()
_content_analyzer = ContentAnalyzerAgent()
_scene_classifier = SceneClassifierAgent()
_metadata_extractor = MetadataExtractorAgent()
_safety_checker = SafetyCheckerAgent()
_report_generator = ReportGeneratorAgent()


# ── Node wrappers (LangGraph expects plain async functions) ───────────────────


def _summarize_orchestrator(updates: dict[str, Any]) -> str:
    frames = updates.get("frames") or []
    tr = updates.get("transcript") or ""
    return f"frames={len(frames)}, transcript_chars={len(tr)}"


def _summarize_content(updates: dict[str, Any]) -> str | None:
    ca = updates.get("content_analysis") or {}
    s = ca.get("summary")
    return str(s)[:200] if s else None


def _summarize_scene(updates: dict[str, Any]) -> str | None:
    sc = updates.get("scene_classifications") or []
    return f"frames_classified={len(sc)}"


def _summarize_metadata(updates: dict[str, Any]) -> str | None:
    m = updates.get("metadata") or {}
    keys = list(m.keys())[:8]
    return f"keys={keys}" if keys else None


def _summarize_safety(updates: dict[str, Any]) -> str | None:
    s = updates.get("safety_result") or {}
    d = s.get("decision")
    return str(d) if d is not None else None


def _summarize_report(updates: dict[str, Any]) -> str | None:
    mr = updates.get("moderation_report") or {}
    d = mr.get("decision")
    return f"decision={d}" if d is not None else None


async def orchestrator_node(state: VideoAnalysisState) -> dict[str, Any]:
    return await run_audited_pipeline_step(
        state,
        agent_id="orchestrator",
        action_type="ORCHESTRATION",
        runner=lambda: _orchestrator.run(dict(state)),
        summarize=_summarize_orchestrator,
    )


async def content_analyzer_node(state: VideoAnalysisState) -> dict[str, Any]:
    return await run_audited_pipeline_step(
        state,
        agent_id="content_analyzer",
        action_type="CONTENT_ANALYSIS",
        runner=lambda: _content_analyzer.run(dict(state)),
        summarize=_summarize_content,
    )


async def scene_classifier_node(state: VideoAnalysisState) -> dict[str, Any]:
    return await run_audited_pipeline_step(
        state,
        agent_id="scene_classifier",
        action_type="SCENE_CLASSIFICATION",
        runner=lambda: _scene_classifier.run(dict(state)),
        summarize=_summarize_scene,
    )


async def metadata_extractor_node(state: VideoAnalysisState) -> dict[str, Any]:
    return await run_audited_pipeline_step(
        state,
        agent_id="metadata_extractor",
        action_type="METADATA_EXTRACTION",
        runner=lambda: _metadata_extractor.run(dict(state)),
        summarize=_summarize_metadata,
    )


async def safety_checker_node(state: VideoAnalysisState) -> dict[str, Any]:
    return await run_audited_pipeline_step(
        state,
        agent_id="safety_checker",
        action_type="SAFETY_EVALUATION",
        runner=lambda: _safety_checker.run(dict(state)),
        summarize=_summarize_safety,
    )


async def report_generator_node(state: VideoAnalysisState) -> dict[str, Any]:
    return await run_audited_pipeline_step(
        state,
        agent_id="report_generator",
        action_type="REPORT_GENERATION",
        runner=lambda: _report_generator.run(dict(state)),
        summarize=_summarize_report,
    )


# ── Build the graph ───────────────────────────────────────────────────────────


def _build_graph() -> Any:
    graph = StateGraph(VideoAnalysisState)

    # Add nodes
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("content_analyzer", content_analyzer_node)
    graph.add_node("scene_classifier", scene_classifier_node)
    graph.add_node("metadata_extractor", metadata_extractor_node)
    graph.add_node("safety_checker", safety_checker_node)
    graph.add_node("report_generator", report_generator_node)

    # Entry point
    graph.set_entry_point("orchestrator")

    # Fan-out: orchestrator → parallel specialists
    graph.add_edge("orchestrator", "content_analyzer")
    graph.add_edge("orchestrator", "scene_classifier")
    graph.add_edge("orchestrator", "metadata_extractor")

    # Fan-in: all three → safety_checker
    graph.add_edge("content_analyzer", "safety_checker")
    graph.add_edge("scene_classifier", "safety_checker")
    graph.add_edge("metadata_extractor", "safety_checker")

    # Final step
    graph.add_edge("safety_checker", "report_generator")
    graph.add_edge("report_generator", END)

    return graph.compile()


_compiled_graph = _build_graph()


# ── Public API ────────────────────────────────────────────────────────────────


async def run_video_analysis(
    video_id: str,
    video_url: str,
    policy_rules: list[dict[str, Any]] | None = None,
    *,
    frames: list[str] | None = None,
    transcript: str | None = None,
) -> ModerationReport:
    """
    Run the full video analysis pipeline and return a ModerationReport.

    Args:
        video_id:     UUID string of the video being analysed.
        video_url:    Presigned S3 URL (or local path) to the video file.
        policy_rules: Active policy rules to enforce. Defaults to [].
        frames:       Pre-extracted base64 frames (optional; skips FFmpeg step).
        transcript:   Pre-generated transcript text (optional; skips Whisper step).

    Returns:
        ModerationReport — the final structured moderation decision.
    """
    trace_id = str(uuid.uuid4())
    initial_state: VideoAnalysisState = {
        "video_id": video_id,
        "trace_id": trace_id,
        "video_url": video_url,
        "policy_rules": policy_rules or [],
        "errors": [],
        "completed_agents": [],
    }

    if frames is not None:
        initial_state["frames"] = frames
        initial_state["frame_timestamps"] = [float(i * 5) for i in range(len(frames))]

    if transcript is not None:
        initial_state["transcript"] = transcript

    logger.info("pipeline_start", video_id=video_id)

    try:
        final_state: VideoAnalysisState = await _compiled_graph.ainvoke(initial_state)
    except Exception as exc:
        logger.error("pipeline_error", video_id=video_id, error=str(exc))
        record_pipeline_audit_sync(
            {"video_id": video_id, "trace_id": trace_id},
            agent_id="video_analysis_pipeline",
            action_type="PIPELINE_FATAL",
            description=f"Pipeline failed: {type(exc).__name__}",
            output_summary=str(exc)[:512],
            status=AgentAuditStatus.FAILED,
            execution_time_ms=None,
        )
        raise

    report_dict = final_state.get("moderation_report") or {}
    if not report_dict:
        # Graph completed but no report was generated — shouldn't happen
        from app.ai.schemas import ModerationDecision, ViolationSeverity

        return ModerationReport(
            video_id=video_id,
            decision=ModerationDecision.NEEDS_REVIEW,
            overall_severity=ViolationSeverity.LOW,
            confidence=0.0,
            content_summary="Pipeline completed without generating a report.",
            processing_errors=list(final_state.get("errors") or []),
            agents_completed=list(final_state.get("completed_agents") or []),
        )

    logger.info(
        "pipeline_done",
        video_id=video_id,
        decision=report_dict.get("decision"),
        agents=final_state.get("completed_agents"),
    )

    return ModerationReport.model_validate(report_dict)
