"""User profile fields and access-control block columns.

Revision ID: 0004_user_profile_access
Revises: 0003_add_source_url
Create Date: 2026-03-24

Adds to the users table:
    - whatsapp_number     VARCHAR(32)   — contact number for notifications
    - is_blocked          BOOLEAN       — permanent block (email cannot re-register)
    - blocked_at          TIMESTAMPTZ   — when the block was applied
    - blocked_reason      VARCHAR(500)  — optional admin note
    - address_line1       VARCHAR(255)
    - address_line2       VARCHAR(255)
    - city                VARCHAR(128)
    - state               VARCHAR(128)
    - postal_code         VARCHAR(32)
    - country             VARCHAR(128)
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_user_profile_access"
down_revision: str | None = "0003_add_source_url"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("whatsapp_number", sa.String(32), nullable=True))
    op.add_column(
        "users",
        sa.Column("is_blocked", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "users",
        sa.Column("blocked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("users", sa.Column("blocked_reason", sa.String(500), nullable=True))
    op.add_column("users", sa.Column("address_line1", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("address_line2", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("city", sa.String(128), nullable=True))
    op.add_column("users", sa.Column("state", sa.String(128), nullable=True))
    op.add_column("users", sa.Column("postal_code", sa.String(32), nullable=True))
    op.add_column("users", sa.Column("country", sa.String(128), nullable=True))
    op.create_index("ix_users_is_blocked", "users", ["is_blocked"])


def downgrade() -> None:
    op.drop_index("ix_users_is_blocked", table_name="users")
    op.drop_column("users", "country")
    op.drop_column("users", "postal_code")
    op.drop_column("users", "state")
    op.drop_column("users", "city")
    op.drop_column("users", "address_line2")
    op.drop_column("users", "address_line1")
    op.drop_column("users", "blocked_reason")
    op.drop_column("users", "blocked_at")
    op.drop_column("users", "is_blocked")
    op.drop_column("users", "whatsapp_number")
