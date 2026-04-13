"""Add source_url column to videos table for web/YouTube URL ingestion.

Revision ID: 0003_add_source_url
Revises: 0002_add_user_name
Create Date: 2026-03-24
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_add_source_url"
down_revision: str | None = "0002_add_user_name"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("videos", sa.Column("source_url", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("videos", "source_url")
