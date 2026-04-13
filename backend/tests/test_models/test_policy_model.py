"""Tests for D-04 Policy model."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from app.models.policy import Policy
from app.models.user import User


def _make_user(db_session):
    u = User(email=f"u{uuid.uuid4()}@test.ai", password_hash="hash")
    db_session.add(u)
    return u


class TestPolicyModel:
    @pytest.mark.asyncio
    async def test_create_policy_with_defaults(self, db_session):
        owner = _make_user(db_session)
        await db_session.flush()

        policy = Policy(name="Default Policy", owner_id=owner.id)
        db_session.add(policy)
        await db_session.flush()

        result = await db_session.execute(select(Policy).where(Policy.name == "Default Policy"))
        p = result.scalar_one()

        assert p.is_active is True
        assert p.is_default is False
        assert p.default_action == "allow"
        assert p.rules is None

    @pytest.mark.asyncio
    async def test_policy_rules_stored_as_json(self, db_session):
        owner = _make_user(db_session)
        await db_session.flush()

        rules = [
            {"category": "violence", "threshold": 0.8, "action": "block"},
            {"category": "nudity", "threshold": 0.9, "action": "flag"},
        ]
        policy = Policy(name="Strict Policy", owner_id=owner.id, rules=rules)
        db_session.add(policy)
        await db_session.flush()

        result = await db_session.execute(select(Policy).where(Policy.name == "Strict Policy"))
        p = result.scalar_one()

        assert isinstance(p.rules, list)
        assert len(p.rules) == 2
        assert p.rules[0]["category"] == "violence"

    @pytest.mark.asyncio
    async def test_policy_is_default_flag(self, db_session):
        owner = _make_user(db_session)
        await db_session.flush()

        policy = Policy(
            name="Global Default",
            owner_id=owner.id,
            is_default=True,
            default_action="block",
        )
        db_session.add(policy)
        await db_session.flush()

        result = await db_session.execute(select(Policy).where(Policy.name == "Global Default"))
        p = result.scalar_one()

        assert p.is_default is True
        assert p.default_action == "block"

    @pytest.mark.asyncio
    async def test_policy_with_tenant(self, db_session):
        owner = _make_user(db_session)
        await db_session.flush()

        policy = Policy(name="Tenant Policy", owner_id=owner.id, tenant_id="tenant-xyz")
        db_session.add(policy)
        await db_session.flush()

        result = await db_session.execute(select(Policy).where(Policy.name == "Tenant Policy"))
        p = result.scalar_one()
        assert p.tenant_id == "tenant-xyz"
