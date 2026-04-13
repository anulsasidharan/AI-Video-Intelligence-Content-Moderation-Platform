"""
Best-effort agent audit rows for the LangGraph video analysis pipeline.

Uses sync DB sessions so Celery workers and asyncio.run() pipelines can persist
without an AsyncSession. Failures are swallowed inside agent_audit_logger.log_sync.
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from app.models.agent_audit import AgentAuditStatus
from app.schemas.agent_audit import AgentAuditCreate
from app.services.agent_audit_service import agent_audit_logger


def _clip(text: str | None, max_len: int) -> str:
    if not text:
        return ""
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


def record_pipeline_audit_sync(
    state: Mapping[str, Any],
    *,
    agent_id: str,
    action_type: str,
    description: str,
    output_summary: str | None,
    status: AgentAuditStatus,
    execution_time_ms: int | None,
    triggered_by: str = "system",
    correlation_id: str | None = None,
) -> None:
    vid = str(state.get("video_id") or "unknown")
    tid = str(state.get("trace_id") or "unknown-trace")
    desc = _clip(description.strip() or "—", 512) or "—"
    event = AgentAuditCreate(
        agent_id=_clip(agent_id, 64) or "unknown",
        action_type=_clip(action_type, 64) or "UNKNOWN",
        description=desc,
        input_ref=_clip(vid, 255) or "unknown",
        output_summary=_clip(output_summary, 512) if output_summary else None,
        status=status,
        execution_time_ms=execution_time_ms,
        triggered_by=_clip(triggered_by, 32) or "system",
        trace_id=_clip(tid, 64) or "unknown",
        correlation_id=_clip(correlation_id, 64) if correlation_id else None,
    )
    agent_audit_logger.log_sync(event)


async def run_audited_pipeline_step(
    state: Mapping[str, Any],
    *,
    agent_id: str,
    action_type: str,
    runner: Callable[[], Awaitable[dict[str, Any]]],
    summarize: Callable[[dict[str, Any]], str | None],
) -> dict[str, Any]:
    """Run an async agent step, record SUCCESS/FAILED to agent_audit_logs."""
    st: dict[str, Any] = dict(state)
    t0 = time.perf_counter()
    try:
        updates = await runner()
        ms = int((time.perf_counter() - t0) * 1000)
        record_pipeline_audit_sync(
            st,
            agent_id=agent_id,
            action_type=action_type,
            description=f"{agent_id} completed",
            output_summary=summarize(updates),
            status=AgentAuditStatus.SUCCESS,
            execution_time_ms=ms,
        )
        return updates
    except Exception as exc:  # noqa: BLE001
        ms = int((time.perf_counter() - t0) * 1000)
        record_pipeline_audit_sync(
            st,
            agent_id=agent_id,
            action_type=action_type,
            description=f"{agent_id} raised {type(exc).__name__}",
            output_summary=_clip(str(exc), 512) or None,
            status=AgentAuditStatus.FAILED,
            execution_time_ms=ms,
        )
        raise
