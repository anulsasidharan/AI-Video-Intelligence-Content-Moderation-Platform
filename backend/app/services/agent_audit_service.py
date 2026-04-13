from __future__ import annotations

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.sync_db import sync_session
from app.models.agent_audit import AgentAuditLog
from app.schemas.agent_audit import AgentAuditCreate

logger = structlog.get_logger(__name__)


class AgentAuditLoggingService:
    """
    Centralized, best-effort persistence of AI agent audit events.

    Security/Resilience:
    - Admin-only read API enforces access at the route layer.
    - Logging failures must never break agent execution paths.
    """

    async def log(self, db: AsyncSession, event: AgentAuditCreate) -> None:
        try:
            row = AgentAuditLog(
                agent_id=event.agent_id,
                action_type=event.action_type,
                description=event.description,
                input_ref=event.input_ref,
                output_summary=event.output_summary,
                status=event.status,
                execution_time_ms=event.execution_time_ms,
                triggered_by=event.triggered_by,
                trace_id=event.trace_id,
                correlation_id=event.correlation_id,
                event_timestamp=event.event_timestamp,
            )
            db.add(row)
            # Best-effort flush so the row participates in caller transaction
            await db.flush()
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "agent_audit_persist_failed",
                agent_id=event.agent_id,
                action_type=event.action_type,
                status=str(event.status),
                error=str(exc),
            )

    def log_sync(self, event: AgentAuditCreate) -> None:
        """
        Persist an audit row using a sync DB session (Celery / asyncio.run pipeline).

        Uses ``app.core.sync_db`` so we never import the Celery app from here.
        """
        try:
            row = AgentAuditLog(
                agent_id=event.agent_id,
                action_type=event.action_type,
                description=event.description,
                input_ref=event.input_ref,
                output_summary=event.output_summary,
                status=event.status,
                execution_time_ms=event.execution_time_ms,
                triggered_by=event.triggered_by,
                trace_id=event.trace_id,
                correlation_id=event.correlation_id,
                event_timestamp=event.event_timestamp,
            )
            with sync_session() as db:
                db.add(row)
            logger.info(
                "agent_audit_persisted_sync",
                agent_id=event.agent_id,
                action_type=event.action_type,
                trace_id=event.trace_id,
                input_ref=event.input_ref,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "agent_audit_persist_sync_failed",
                agent_id=event.agent_id,
                action_type=event.action_type,
                status=str(event.status),
                error=str(exc),
            )


agent_audit_logger = AgentAuditLoggingService()
