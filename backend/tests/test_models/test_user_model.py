"""Tests for D-01 User model."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models.user import User, UserRole


class TestUserModel:
    @pytest.mark.asyncio
    async def test_create_user_with_defaults(self, db_session):
        user = User(
            email="test@vidshield.ai",
            password_hash="hashed_password",
        )
        db_session.add(user)
        await db_session.flush()

        result = await db_session.execute(select(User).where(User.email == "test@vidshield.ai"))
        fetched = result.scalar_one_or_none()

        assert fetched is not None
        assert fetched.email == "test@vidshield.ai"
        assert fetched.role == UserRole.OPERATOR
        assert fetched.is_active is True
        assert fetched.id is not None
        assert fetched.created_at is not None

    @pytest.mark.asyncio
    async def test_user_role_enum_values(self, db_session):
        admin = User(email="admin@vidshield.ai", password_hash="hash", role=UserRole.ADMIN)
        api = User(email="api@vidshield.ai", password_hash="hash", role=UserRole.API_CONSUMER)
        db_session.add(admin)
        db_session.add(api)
        await db_session.flush()

        result = await db_session.execute(select(User).where(User.email == "admin@vidshield.ai"))
        fetched_admin = result.scalar_one()
        assert fetched_admin.role == UserRole.ADMIN

        result = await db_session.execute(select(User).where(User.email == "api@vidshield.ai"))
        fetched_api = result.scalar_one()
        assert fetched_api.role == UserRole.API_CONSUMER

    @pytest.mark.asyncio
    async def test_user_can_be_deactivated(self, db_session):
        user = User(email="inactive@vidshield.ai", password_hash="hash", is_active=False)
        db_session.add(user)
        await db_session.flush()

        result = await db_session.execute(select(User).where(User.email == "inactive@vidshield.ai"))
        fetched = result.scalar_one()
        assert fetched.is_active is False

    @pytest.mark.asyncio
    async def test_user_with_tenant_id(self, db_session):
        user = User(
            email="tenant@vidshield.ai",
            password_hash="hash",
            tenant_id="tenant-abc-123",
        )
        db_session.add(user)
        await db_session.flush()

        result = await db_session.execute(select(User).where(User.email == "tenant@vidshield.ai"))
        fetched = result.scalar_one()
        assert fetched.tenant_id == "tenant-abc-123"
