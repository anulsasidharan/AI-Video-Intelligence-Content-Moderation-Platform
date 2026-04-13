"""
LangGraph shared state for the video analysis pipeline.

All agents read from and write to this TypedDict. LangGraph merges
partial updates returned by each node automatically.

Fields updated by parallel nodes (completed_agents, errors) must use
Annotated with a reducer so LangGraph can merge concurrent writes.
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class VideoAnalysisState(TypedDict, total=False):
    # ── Input ─────────────────────────────────────────────────────────────────
    video_id: str
    trace_id: str  # correlates agent_audit_logs for one pipeline run
    video_url: str  # presigned S3 URL or local path
    policy_rules: list[dict[str, Any]]  # active policy rules loaded by orchestrator

    # ── Frame data ────────────────────────────────────────────────────────────
    frames: list[str]  # base64-encoded JPEG frames sampled from the video
    frame_timestamps: list[float]  # seconds from start for each frame

    # ── Audio / transcript ────────────────────────────────────────────────────
    transcript: str  # raw Whisper transcript text
    transcript_segments: list[dict[str, Any]]  # [{start, end, text}, ...]

    # ── Agent outputs ─────────────────────────────────────────────────────────
    content_analysis: dict[str, Any]  # ContentAnalyzer result
    safety_result: dict[str, Any]  # SafetyChecker result
    metadata: dict[str, Any]  # MetadataExtractor result
    scene_classifications: list[dict[str, Any]]  # SceneClassifier per-frame results
    moderation_report: dict[str, Any]  # ReportGenerator final report

    # ── Control — use operator.add reducer to handle concurrent writes ─────────
    errors: Annotated[list[str], operator.add]
    completed_agents: Annotated[list[str], operator.add]
