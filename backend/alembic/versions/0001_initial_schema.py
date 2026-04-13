"""Initial schema — all core tables.

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2026-03-18

Creates the full VidShield AI database schema:
    users, policies, videos, live_streams, moderation_results,
    moderation_queue, alerts, analytics_events, webhook_endpoints.

All enum columns use VARCHAR (native_enum=False) so no PostgreSQL
ENUM types are created — values are validated at the application layer.

Tables are created in FK-dependency order and dropped in reverse.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── 1. users ───────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "role",
            sa.String(64),
            nullable=False,
            server_default="operator",
        ),
        sa.Column("tenant_id", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
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
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])
    op.create_index("ix_users_role", "users", ["role"])

    # ── 2. policies ────────────────────────────────────────────────────────────
    op.create_table(
        "policies",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("rules", sa.JSON(), nullable=True),
        sa.Column("default_action", sa.String(64), nullable=False, server_default="allow"),
        sa.Column(
            "owner_id",
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
    op.create_index("ix_policies_owner_id", "policies", ["owner_id"])
    op.create_index("ix_policies_tenant_id", "policies", ["tenant_id"])

    # ── 3. videos ──────────────────────────────────────────────────────────────
    op.create_table(
        "videos",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(32),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "source",
            sa.String(32),
            nullable=False,
            server_default="upload",
        ),
        sa.Column("s3_key", sa.String(1024), nullable=True),
        sa.Column("thumbnail_s3_key", sa.String(1024), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("content_type", sa.String(128), nullable=True),
        sa.Column("tags", sa.Text(), nullable=True),
        sa.Column(
            "owner_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tenant_id", sa.String(255), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("deleted_at", sa.String(64), nullable=True),
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
    op.create_index("ix_videos_owner_id", "videos", ["owner_id"])
    op.create_index("ix_videos_tenant_id", "videos", ["tenant_id"])
    op.create_index("ix_videos_status", "videos", ["status"])

    # ── 4. live_streams ────────────────────────────────────────────────────────
    op.create_table(
        "live_streams",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("ingest_url", sa.String(1024), nullable=True),
        sa.Column(
            "status",
            sa.String(32),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "owner_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tenant_id", sa.String(255), nullable=True),
        sa.Column("stopped_at", sa.String(64), nullable=True),
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
    op.create_index("ix_live_streams_owner_id", "live_streams", ["owner_id"])
    op.create_index("ix_live_streams_tenant_id", "live_streams", ["tenant_id"])
    op.create_index("ix_live_streams_status", "live_streams", ["status"])

    # ── 5. moderation_results ──────────────────────────────────────────────────
    op.create_table(
        "moderation_results",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "video_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("videos.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "status",
            sa.String(32),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("overall_confidence", sa.Float(), nullable=True),
        sa.Column("violations", sa.JSON(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("ai_model", sa.String(128), nullable=True),
        sa.Column("processing_time_ms", sa.Integer(), nullable=True),
        # Human review
        sa.Column(
            "reviewed_by",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("review_action", sa.String(32), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.String(64), nullable=True),
        # Admin override
        sa.Column(
            "override_by",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("override_decision", sa.String(64), nullable=True),
        sa.Column("override_at", sa.String(64), nullable=True),
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
    op.create_index("ix_moderation_results_video_id", "moderation_results", ["video_id"])
    op.create_index("ix_moderation_results_status", "moderation_results", ["status"])

    # ── 6. moderation_queue ────────────────────────────────────────────────────
    op.create_table(
        "moderation_queue",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "video_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("videos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "moderation_result_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("moderation_results.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(32),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "assigned_to",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
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
    op.create_index("ix_moderation_queue_video_id", "moderation_queue", ["video_id"])
    op.create_index("ix_moderation_queue_status", "moderation_queue", ["status"])
    op.create_index("ix_moderation_queue_tenant_id", "moderation_queue", ["tenant_id"])

    # ── 7. alerts ──────────────────────────────────────────────────────────────
    op.create_table(
        "alerts",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "stream_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("live_streams.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "severity",
            sa.String(32),
            nullable=False,
            server_default="medium",
        ),
        sa.Column("category", sa.String(128), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("frame_url", sa.String(1024), nullable=True),
        sa.Column("is_dismissed", sa.Boolean(), nullable=False, server_default=sa.false()),
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
    op.create_index("ix_alerts_stream_id", "alerts", ["stream_id"])
    op.create_index("ix_alerts_tenant_id", "alerts", ["tenant_id"])

    # ── 8. analytics_events ────────────────────────────────────────────────────
    op.create_table(
        "analytics_events",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column(
            "video_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("videos.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("tenant_id", sa.String(255), nullable=True),
        sa.Column("category", sa.String(128), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("extra", sa.String(1024), nullable=True),
        sa.Column("event_date", sa.String(10), nullable=False),
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
    op.create_index("ix_analytics_events_event_type", "analytics_events", ["event_type"])
    op.create_index("ix_analytics_events_video_id", "analytics_events", ["video_id"])
    op.create_index("ix_analytics_events_tenant_id", "analytics_events", ["tenant_id"])
    op.create_index("ix_analytics_events_category", "analytics_events", ["category"])
    op.create_index("ix_analytics_events_event_date", "analytics_events", ["event_date"])

    # ── 9. webhook_endpoints ───────────────────────────────────────────────────
    op.create_table(
        "webhook_endpoints",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("secret", sa.String(512), nullable=True),
        sa.Column("events", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("total_deliveries", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_deliveries", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_delivery_at", sa.String(64), nullable=True),
        sa.Column("last_status_code", sa.Integer(), nullable=True),
        sa.Column(
            "owner_id",
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
    op.create_index("ix_webhook_endpoints_owner_id", "webhook_endpoints", ["owner_id"])
    op.create_index("ix_webhook_endpoints_tenant_id", "webhook_endpoints", ["tenant_id"])


def downgrade() -> None:
    # Drop in reverse FK-dependency order
    op.drop_table("webhook_endpoints")
    op.drop_table("analytics_events")
    op.drop_table("alerts")
    op.drop_table("moderation_queue")
    op.drop_table("moderation_results")
    op.drop_table("live_streams")
    op.drop_table("videos")
    op.drop_table("policies")
    op.drop_table("users")
