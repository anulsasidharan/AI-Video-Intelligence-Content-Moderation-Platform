"""Tests for S-01 AuthService — all DB and Redis calls mocked."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import ConflictError, UnauthorizedError

# ── Helpers ────────────────────────────────────────────────────────────────────


def _make_user(user_id: str | None = None, email: str = "user@test.com", active: bool = True):
    user = MagicMock()
    user.id = uuid.UUID(user_id) if user_id else uuid.uuid4()
    user.email = email
    user.is_active = active
    user.role.value = "viewer"
    user.password_hash = "hashed_password"
    return user


def _make_db(user_result=None):
    """Return a mock AsyncSession with scalar_one_or_none patched."""
    db = AsyncMock()
    scalar_mock = MagicMock()
    scalar_mock.scalar_one_or_none.return_value = user_result
    db.execute = AsyncMock(return_value=scalar_mock)
    db.add = MagicMock()
    db.flush = AsyncMock()
    return db


def _make_redis():
    redis = AsyncMock()
    redis.setex = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.delete = AsyncMock(return_value=1)
    return redis


# ── register ───────────────────────────────────────────────────────────────────


class TestRegister:
    @pytest.mark.asyncio
    async def test_registers_new_user_and_issues_tokens(self):
        from app.models.user import UserRole
        from app.services.auth_service import AuthService

        db = _make_db(user_result=None)  # no existing user
        redis = _make_redis()

        expected_id = uuid.uuid4()

        def _inject_user_attrs(user_obj):
            user_obj.id = expected_id
            user_obj.role = UserRole.API_CONSUMER

        db.add = MagicMock(side_effect=_inject_user_attrs)

        mock_login_response = MagicMock()
        mock_login_response.access_token = "access_tok"
        mock_login_response.refresh_token = "refresh_tok"

        with (
            patch("app.services.auth_service.hash_password", return_value="hashed"),
            patch(
                "app.services.auth_service.create_access_token",
                return_value="access_tok",
            ),
            patch(
                "app.services.auth_service.create_refresh_token",
                return_value="refresh_tok",
            ),
            patch(
                "app.services.auth_service.refresh_token_key",
                return_value="key:refresh_tok",
            ),
            patch("app.services.auth_service.UserResponse") as MockUserResp,
            patch(
                "app.services.auth_service.LoginResponse",
                return_value=mock_login_response,
            ),
        ):
            MockUserResp.model_validate.return_value = MagicMock()

            service = AuthService(db=db, redis=redis)
            result = await service.register(email="new@test.com", password="pass")

        db.add.assert_called_once()
        db.flush.assert_awaited_once()
        redis.setex.assert_awaited_once()
        assert result.access_token == "access_tok"
        assert result.refresh_token == "refresh_tok"

    @pytest.mark.asyncio
    async def test_raises_conflict_on_duplicate_email(self):
        from app.services.auth_service import AuthService

        existing_user = _make_user(email="dup@test.com")
        db = _make_db(user_result=existing_user)
        redis = _make_redis()

        service = AuthService(db=db, redis=redis)
        with pytest.raises(ConflictError, match="already registered"):
            await service.register(email="dup@test.com", password="pass")


# ── login ──────────────────────────────────────────────────────────────────────


class TestLogin:
    @pytest.mark.asyncio
    async def test_returns_tokens_on_valid_credentials(self):
        from app.services.auth_service import AuthService

        user = _make_user()
        db = _make_db(user_result=user)
        redis = _make_redis()

        mock_login_response = MagicMock()
        mock_login_response.access_token = "access"
        mock_login_response.refresh_token = "refresh"

        with (
            patch("app.services.auth_service.verify_password", return_value=True),
            patch("app.services.auth_service.create_access_token", return_value="access"),
            patch("app.services.auth_service.create_refresh_token", return_value="refresh"),
            patch("app.services.auth_service.refresh_token_key", return_value="key:r"),
            patch("app.services.auth_service.UserResponse") as MockUserResp,
            patch(
                "app.services.auth_service.LoginResponse",
                return_value=mock_login_response,
            ),
        ):
            MockUserResp.model_validate.return_value = MagicMock()

            service = AuthService(db=db, redis=redis)
            result = await service.login(email=user.email, password="correct")

        assert result.access_token == "access"
        assert result.refresh_token == "refresh"

    @pytest.mark.asyncio
    async def test_raises_unauthorized_on_wrong_password(self):
        from app.services.auth_service import AuthService

        user = _make_user()
        db = _make_db(user_result=user)
        redis = _make_redis()

        with patch("app.services.auth_service.verify_password", return_value=False):
            service = AuthService(db=db, redis=redis)
            with pytest.raises(UnauthorizedError):
                await service.login(email=user.email, password="wrong")

    @pytest.mark.asyncio
    async def test_raises_unauthorized_when_user_not_found(self):
        from app.services.auth_service import AuthService

        db = _make_db(user_result=None)
        redis = _make_redis()

        service = AuthService(db=db, redis=redis)
        with pytest.raises(UnauthorizedError):
            await service.login(email="ghost@test.com", password="any")


# ── refresh_tokens ─────────────────────────────────────────────────────────────


class TestRefreshTokens:
    @pytest.mark.asyncio
    async def test_rotates_tokens_on_valid_refresh(self):
        from app.services.auth_service import AuthService

        user = _make_user()
        db = _make_db(user_result=user)
        redis = _make_redis()
        redis.get = AsyncMock(return_value=str(user.id))

        with (
            patch(
                "app.services.auth_service.decode_token",
                return_value={"type": "refresh", "sub": str(user.id)},
            ),
            patch("app.services.auth_service.refresh_token_key", return_value="key:old"),
            patch(
                "app.services.auth_service.create_access_token",
                return_value="new_access",
            ),
            patch(
                "app.services.auth_service.create_refresh_token",
                return_value="new_refresh",
            ),
        ):
            service = AuthService(db=db, redis=redis)
            result = await service.refresh_tokens("old_refresh_token")

        redis.delete.assert_awaited()
        assert result.access_token == "new_access"
        assert result.refresh_token == "new_refresh"

    @pytest.mark.asyncio
    async def test_raises_unauthorized_on_revoked_token(self):
        from app.services.auth_service import AuthService

        db = _make_db()
        redis = _make_redis()
        redis.get = AsyncMock(return_value=None)  # key not in Redis → revoked

        with (
            patch(
                "app.services.auth_service.decode_token",
                return_value={"type": "refresh"},
            ),
            patch("app.services.auth_service.refresh_token_key", return_value="key:r"),
        ):
            service = AuthService(db=db, redis=redis)
            with pytest.raises(UnauthorizedError, match="revoked"):
                await service.refresh_tokens("revoked_token")

    @pytest.mark.asyncio
    async def test_raises_unauthorized_on_wrong_token_type(self):
        from app.services.auth_service import AuthService

        db = _make_db()
        redis = _make_redis()

        with patch("app.services.auth_service.decode_token", return_value={"type": "access"}):
            service = AuthService(db=db, redis=redis)
            with pytest.raises(UnauthorizedError, match="token type"):
                await service.refresh_tokens("access_token_passed_as_refresh")


# ── logout ─────────────────────────────────────────────────────────────────────


class TestLogout:
    @pytest.mark.asyncio
    async def test_deletes_redis_key_on_logout(self):
        from app.services.auth_service import AuthService

        db = _make_db()
        redis = _make_redis()

        with patch("app.services.auth_service.refresh_token_key", return_value="key:r"):
            service = AuthService(db=db, redis=redis)
            await service.logout("some_refresh_token")

        redis.delete.assert_awaited_once_with("key:r")
