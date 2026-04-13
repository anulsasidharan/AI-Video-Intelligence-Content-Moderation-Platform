"""Add live stream moderation control columns and alert confidence.

Revision ID: 0013_live_stream_moderation
Revises: 0012_password_reset_tokens
Create Date: 2026-03-27
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0013_live_stream_moderation"
down_revision: str | None = "0012_password_reset_tokens"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # live_streams — moderation control columns
    op.add_column(
        "live_streams",
        sa.Column("moderation_active", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "live_streams",
        sa.Column("moderation_started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "live_streams",
        sa.Column("moderation_stopped_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "live_streams",
        sa.Column("frames_processed", sa.Integer(), nullable=False, server_default="0"),
    )

    # alerts — confidence score
    op.add_column("alerts", sa.Column("confidence", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("alerts", "confidence")
    op.drop_column("live_streams", "frames_processed")
    op.drop_column("live_streams", "moderation_stopped_at")
    op.drop_column("live_streams", "moderation_started_at")
    op.drop_column("live_streams", "moderation_active")
