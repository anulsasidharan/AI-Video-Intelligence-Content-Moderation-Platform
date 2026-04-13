"""Create report_templates and report_jobs tables.

Revision ID: 0008_report_tables
Revises: 0007_agent_audit_logs
Create Date: 2026-03-25

report_templates: saved report configurations (name, type, filters, columns, orientation).
report_jobs:      per-generation run record tracking async status, S3 location, and audit trail.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008_report_tables"
down_revision: str | None = "0007_agent_audit_logs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── report_templates ──────────────────────────────────────────────────────
    op.create_table(
        "report_templates",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("report_type", sa.String(64), nullable=False),
        sa.Column("filters", sa.Text, nullable=True),
        sa.Column("columns", sa.Text, nullable=True),
        sa.Column("orientation", sa.String(32), nullable=False, server_default="portrait"),
        sa.Column(
            "owner_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("is_shared", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("tenant_id", sa.String(255), nullable=True),
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
    op.create_index("ix_report_templates_owner_id", "report_templates", ["owner_id"])
    op.create_index("ix_report_templates_report_type", "report_templates", ["report_type"])
    op.create_index("ix_report_templates_tenant_id", "report_templates", ["tenant_id"])

    # ── report_jobs ───────────────────────────────────────────────────────────
    op.create_table(
        "report_jobs",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("report_type", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("filters", sa.Text, nullable=True),
        sa.Column("columns", sa.Text, nullable=True),
        sa.Column("orientation", sa.String(32), nullable=False, server_default="portrait"),
        sa.Column("s3_key", sa.String(1024), nullable=True),
        sa.Column("file_size_bytes", sa.Integer, nullable=True),
        sa.Column("row_count", sa.Integer, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column(
            "template_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("report_templates.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "generated_by",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tenant_id", sa.String(255), nullable=True),
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
    op.create_index("ix_report_jobs_generated_by", "report_jobs", ["generated_by"])
    op.create_index("ix_report_jobs_report_type", "report_jobs", ["report_type"])
    op.create_index("ix_report_jobs_status", "report_jobs", ["status"])
    op.create_index("ix_report_jobs_tenant_id", "report_jobs", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_report_jobs_tenant_id", table_name="report_jobs")
    op.drop_index("ix_report_jobs_status", table_name="report_jobs")
    op.drop_index("ix_report_jobs_report_type", table_name="report_jobs")
    op.drop_index("ix_report_jobs_generated_by", table_name="report_jobs")
    op.drop_table("report_jobs")

    op.drop_index("ix_report_templates_tenant_id", table_name="report_templates")
    op.drop_index("ix_report_templates_report_type", table_name="report_templates")
    op.drop_index("ix_report_templates_owner_id", table_name="report_templates")
    op.drop_table("report_templates")
