import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class AgentAuditStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    IN_PROGRESS = "IN_PROGRESS"


class AgentAuditLog(Base, UUIDMixin, TimestampMixin):
    """
    Persistent audit trail of AI agent activities.

    This is used by the Admin Portal "Agent Audit" tab to answer:
    who (agent), what (action), when (timestamp), why (description),
    and how it performed (execution time), with trace correlation.
    """

    __tablename__ = "agent_audit_logs"

    agent_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(512), nullable=False)

    input_ref: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    output_summary: Mapped[str | None] = mapped_column(String(512), nullable=True)

    status: Mapped[AgentAuditStatus] = mapped_column(
        Enum(AgentAuditStatus, name="agent_audit_status_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    triggered_by: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    # optional: allow storing a canonical event timestamp that can differ
    # from created_at in rare backfill scenarios.
    event_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
