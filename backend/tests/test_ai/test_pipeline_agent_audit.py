"""Unit tests for pipeline agent audit helpers (no database)."""

from __future__ import annotations

import pytest

from app.ai.pipeline_agent_audit import run_audited_pipeline_step
from app.models.agent_audit import AgentAuditStatus
from app.services.agent_audit_service import AgentAuditLoggingService


@pytest.mark.asyncio
async def test_run_audited_pipeline_step_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list = []

    def _capture(self: AgentAuditLoggingService, event: object) -> None:
        captured.append(event)

    monkeypatch.setattr(AgentAuditLoggingService, "log_sync", _capture)

    async def _runner() -> dict:
        return {"ok": True}

    out = await run_audited_pipeline_step(
        {"video_id": "vid-1", "trace_id": "trace-1"},
        agent_id="test_agent",
        action_type="TEST_ACTION",
        runner=_runner,
        summarize=lambda u: "done",
    )
    assert out == {"ok": True}
    assert len(captured) == 1
    ev = captured[0]
    assert ev.agent_id == "test_agent"
    assert ev.action_type == "TEST_ACTION"
    assert ev.status == AgentAuditStatus.SUCCESS
    assert ev.execution_time_ms is not None


@pytest.mark.asyncio
async def test_run_audited_pipeline_step_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list = []

    def _capture(self: AgentAuditLoggingService, event: object) -> None:
        captured.append(event)

    monkeypatch.setattr(AgentAuditLoggingService, "log_sync", _capture)

    async def _runner() -> dict:
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        await run_audited_pipeline_step(
            {"video_id": "vid-2", "trace_id": "trace-2"},
            agent_id="failing_agent",
            action_type="FAIL_ACTION",
            runner=_runner,
            summarize=lambda u: None,
        )
    assert len(captured) == 1
    assert captured[0].status == AgentAuditStatus.FAILED
