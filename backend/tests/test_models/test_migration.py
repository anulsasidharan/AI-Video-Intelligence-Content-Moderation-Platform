"""Tests for D-07 Alembic migration structure."""

from __future__ import annotations

import pytest

from app.models.base import Base


class TestMigrationStructure:
    def test_all_expected_tables_in_metadata(self):
        """Verify all 9 tables defined in models are registered in Base.metadata."""
        expected_tables = {
            "users",
            "policies",
            "videos",
            "live_streams",
            "moderation_results",
            "moderation_queue",
            "alerts",
            "analytics_events",
            "webhook_endpoints",
        }
        # Import all models to ensure they register with Base
        import app.models.alert  # noqa: F401
        import app.models.analytics  # noqa: F401
        import app.models.moderation  # noqa: F401
        import app.models.policy  # noqa: F401
        import app.models.user  # noqa: F401
        import app.models.video  # noqa: F401
        import app.models.webhook  # noqa: F401

        actual_tables = set(Base.metadata.tables.keys())
        assert expected_tables.issubset(
            actual_tables
        ), f"Missing tables: {expected_tables - actual_tables}"

    def _load_migration(self):
        import importlib.util
        import pathlib

        migration_path = (
            pathlib.Path(__file__).parent.parent.parent
            / "alembic"
            / "versions"
            / "0001_initial_schema.py"
        )
        spec = importlib.util.spec_from_file_location("migration_0001", migration_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_migration_revision_id(self):
        """Verify migration file has the correct revision identifier."""
        migration = self._load_migration()
        assert migration.revision == "0001_initial_schema"
        assert migration.down_revision is None

    def test_migration_has_upgrade_and_downgrade(self):
        """Verify migration defines both upgrade() and downgrade() functions."""
        migration = self._load_migration()
        assert callable(migration.upgrade)
        assert callable(migration.downgrade)

    @pytest.mark.asyncio
    async def test_schema_created_from_metadata(self, db_session):
        """Verify SQLite can create all tables from Base.metadata (smoke test)."""
        from sqlalchemy import text

        # Tables are already created by the db_session fixture
        # Execute a simple query against each table to confirm existence
        tables_to_check = [
            "users",
            "policies",
            "videos",
            "live_streams",
            "moderation_results",
            "moderation_queue",
            "alerts",
            "analytics_events",
            "webhook_endpoints",
        ]
        for table_name in tables_to_check:
            result = await db_session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            count = result.scalar()
            assert count == 0, f"Table {table_name} should exist and be empty"
