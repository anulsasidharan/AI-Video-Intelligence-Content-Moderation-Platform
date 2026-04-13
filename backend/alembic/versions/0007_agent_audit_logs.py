"""Create agent_audit_logs table for AI agent activity observability.

Revision ID: 0007_agent_audit_logs
Revises: 0006_api_keys
Create Date: 2026-03-25

Stores structured audit entries for AI agent activities (agent_id, action_type,
status, input_ref, output_summary) with trace/correlation ids for workflow
debugging and admin observability.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007_agent_audit_logs"
down_revision: str | None = "0006_api_keys"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_audit_logs",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("agent_id", sa.String(64), nullable=False),
        sa.Column("action_type", sa.String(64), nullable=False),
        sa.Column("description", sa.String(512), nullable=False),
        sa.Column("input_ref", sa.String(255), nullable=False),
        sa.Column("output_summary", sa.String(512), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("execution_time_ms", sa.Integer, nullable=True),
        sa.Column("triggered_by", sa.String(32), nullable=False),
        sa.Column("trace_id", sa.String(64), nullable=False),
        sa.Column("correlation_id", sa.String(64), nullable=True),
        sa.Column("event_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index("ix_agent_audit_logs_agent_id", "agent_audit_logs", ["agent_id"])
    op.create_index("ix_agent_audit_logs_action_type", "agent_audit_logs", ["action_type"])
    op.create_index("ix_agent_audit_logs_status", "agent_audit_logs", ["status"])
    op.create_index("ix_agent_audit_logs_input_ref", "agent_audit_logs", ["input_ref"])
    op.create_index("ix_agent_audit_logs_triggered_by", "agent_audit_logs", ["triggered_by"])
    op.create_index("ix_agent_audit_logs_trace_id", "agent_audit_logs", ["trace_id"])
    op.create_index("ix_agent_audit_logs_correlation_id", "agent_audit_logs", ["correlation_id"])
    op.create_index("ix_agent_audit_logs_event_timestamp", "agent_audit_logs", ["event_timestamp"])
    op.create_index("ix_agent_audit_logs_created_at", "agent_audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_agent_audit_logs_created_at", table_name="agent_audit_logs")
    op.drop_index("ix_agent_audit_logs_event_timestamp", table_name="agent_audit_logs")
    op.drop_index("ix_agent_audit_logs_correlation_id", table_name="agent_audit_logs")
    op.drop_index("ix_agent_audit_logs_trace_id", table_name="agent_audit_logs")
    op.drop_index("ix_agent_audit_logs_triggered_by", table_name="agent_audit_logs")
    op.drop_index("ix_agent_audit_logs_input_ref", table_name="agent_audit_logs")
    op.drop_index("ix_agent_audit_logs_status", table_name="agent_audit_logs")
    op.drop_index("ix_agent_audit_logs_action_type", table_name="agent_audit_logs")
    op.drop_index("ix_agent_audit_logs_agent_id", table_name="agent_audit_logs")
    op.drop_table("agent_audit_logs")
