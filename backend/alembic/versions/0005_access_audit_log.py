"""Create access_audit_logs table for login/logout audit trail.

Revision ID: 0005_access_audit_log
Revises: 0004_user_profile_access
Create Date: 2026-03-24

Creates access_audit_logs for recording login/logout attempts including IP address,
user-agent, status, and failure reason.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005_access_audit_log"
down_revision: str | None = "0004_user_profile_access"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "access_audit_logs",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("failure_reason", sa.String(128), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
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
    op.create_index("ix_access_audit_logs_user_id", "access_audit_logs", ["user_id"])
    op.create_index("ix_access_audit_logs_email", "access_audit_logs", ["email"])
    op.create_index("ix_access_audit_logs_action", "access_audit_logs", ["action"])
    op.create_index("ix_access_audit_logs_status", "access_audit_logs", ["status"])
    op.create_index("ix_access_audit_logs_created_at", "access_audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_access_audit_logs_created_at", table_name="access_audit_logs")
    op.drop_index("ix_access_audit_logs_status", table_name="access_audit_logs")
    op.drop_index("ix_access_audit_logs_action", table_name="access_audit_logs")
    op.drop_index("ix_access_audit_logs_email", table_name="access_audit_logs")
    op.drop_index("ix_access_audit_logs_user_id", table_name="access_audit_logs")
    op.drop_table("access_audit_logs")
