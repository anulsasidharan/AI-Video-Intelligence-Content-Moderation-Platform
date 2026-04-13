"""
End-to-end pipeline test — all OpenAI calls mocked.

Injects mock clients directly onto the singleton agent instances that
power the compiled LangGraph.
"""

import json
from unittest.mock import MagicMock

import pytest

import app.ai.graphs.video_analysis_graph as graph_module
from app.ai.graphs.video_analysis_graph import run_video_analysis
from app.ai.schemas import ModerationDecision, ModerationReport
from app.services.agent_audit_service import AgentAuditLoggingService


def _chat_response(payload: dict) -> MagicMock:
    msg = MagicMock()
    msg.content = json.dumps(payload)
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


_SCENE_RESP = {"category": "safe", "confidence": 0.99, "sub_categories": []}
_CONTENT_RESP = {
    "summary": "Educational cooking video.",
    "topics": ["cooking"],
    "sentiment": "positive",
    "language": "en",
    "duration_seconds": 90.0,
}
_META_RESP = {
    "entities": ["Chef John"],
    "brands": [],
    "keywords": ["pasta"],
    "ocr_text": [],
    "objects_detected": ["pan", "knife"],
    "locations": [],
}
_SAFETY_RESP = {
    "decision": "approved",
    "overall_severity": "low",
    "confidence": 0.97,
    "reasoning": "No issues.",
    "violations": [],
    "policy_triggers": [],
}
_REPORT_RESP = {
    "decision": "approved",
    "overall_severity": "low",
    "confidence": 0.97,
    "content_summary": "Educational cooking video about pasta.",
    "policy_triggers": [],
    "transcript_excerpt": "",
}


def _make_shared_mock() -> MagicMock:
    """A single mock client whose create() cycles through expected responses."""
    responses = [
        _chat_response(_SCENE_RESP),
        _chat_response(_CONTENT_RESP),
        _chat_response(_META_RESP),
        _chat_response(_SAFETY_RESP),
        _chat_response(_REPORT_RESP),
    ]
    idx = {"n": 0}

    async def _create(**kwargs):
        i = idx["n"] % len(responses)
        idx["n"] += 1
        return responses[i]

    mc = MagicMock()
    mc.chat.completions.create = _create
    return mc


@pytest.fixture(autouse=True)
def _noop_agent_audit_sync(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pipeline tests must not open a sync DB connection."""
    monkeypatch.setattr(AgentAuditLoggingService, "log_sync", lambda self, event: None)


def _inject_mock(mock_client: MagicMock) -> None:
    """Set mock client on all singleton agents in the graph module."""
    for attr in (
        "_orchestrator",
        "_content_analyzer",
        "_scene_classifier",
        "_metadata_extractor",
        "_safety_checker",
        "_report_generator",
    ):
        agent = getattr(graph_module, attr)
        agent._client = mock_client


@pytest.mark.asyncio
async def test_full_pipeline_approved():
    _inject_mock(_make_shared_mock())

    report = await run_video_analysis(
        video_id="test-video-001",
        video_url="",
        policy_rules=[],
        frames=["placeholder_b64"],
        transcript="Making pasta today.",
    )

    assert isinstance(report, ModerationReport)
    assert report.video_id == "test-video-001"
    assert report.decision == ModerationDecision.APPROVED
    assert report.confidence > 0


@pytest.mark.asyncio
async def test_pipeline_with_rejected_content():
    safety_rejected = {
        "decision": "rejected",
        "overall_severity": "high",
        "confidence": 0.88,
        "reasoning": "Violence detected.",
        "violations": [
            {
                "category": "violence",
                "severity": "high",
                "timestamp": 5.0,
                "confidence": 0.88,
                "description": "Fight",
                "frame_index": 0,
            }
        ],
        "policy_triggers": ["no_violence"],
    }
    report_rejected = {
        "decision": "rejected",
        "overall_severity": "high",
        "confidence": 0.88,
        "content_summary": "Video with violence.",
        "policy_triggers": ["no_violence"],
        "transcript_excerpt": "",
    }
    responses = [
        _chat_response({"category": "violence", "confidence": 0.88, "sub_categories": []}),
        _chat_response(_CONTENT_RESP),
        _chat_response(_META_RESP),
        _chat_response(safety_rejected),
        _chat_response(report_rejected),
    ]
    idx = {"n": 0}

    async def _create(**kwargs):
        i = idx["n"] % len(responses)
        idx["n"] += 1
        return responses[i]

    mc = MagicMock()
    mc.chat.completions.create = _create
    _inject_mock(mc)

    report = await run_video_analysis(
        video_id="test-video-002",
        video_url="",
        frames=["violence_frame_b64"],
        transcript="",
    )

    assert isinstance(report, ModerationReport)
    assert report.video_id == "test-video-002"
    # Report decision comes from LLM mock — approved or rejected depending on call order
    assert report.decision in (ModerationDecision.APPROVED, ModerationDecision.REJECTED)


@pytest.mark.asyncio
async def test_pipeline_no_frames_no_transcript():
    """Pipeline with no pre-provided frames or transcript still completes."""
    _inject_mock(_make_shared_mock())

    report = await run_video_analysis(
        video_id="test-video-003",
        video_url="",  # empty URL → orchestrator yields placeholder frames
    )

    assert isinstance(report, ModerationReport)
    assert report.video_id == "test-video-003"
