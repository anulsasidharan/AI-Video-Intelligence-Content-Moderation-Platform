"""
S-01 AuthService

Handles all authentication business logic: user registration, login,
JWT token issuance/rotation, and logout. Routes call this service and
stay thin.

Public API:
    await service.register(body)          -> LoginResponse
    await service.login(body)             -> LoginResponse
    await service.refresh_tokens(body)    -> TokenPair
    await service.logout(refresh_token)   -> None
"""

from __future__ import annotations

import uuid
from datetime import timedelta

import redis.asyncio as aioredis
import structlog
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    refresh_token_key,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import LoginResponse, TokenPair
from app.schemas.user import UserResponse

logger = structlog.get_logger(__name__)


class AuthService:
    """Authentication and token-lifecycle service."""

    def __init__(self, db: AsyncSession, redis: aioredis.Redis) -> None:
        self._db = db
        self._redis = redis

    # ── Helpers ────────────────────────────────────────────────────────────────

    async def _issue_token_pair(self, user: User) -> tuple[str, str]:
        """Issue an access + refresh token pair and store the refresh key in Redis."""
        user_id = str(user.id)
        access_token = create_access_token(user_id, extra={"role": user.role.value})
        refresh_token = create_refresh_token(user_id)
        await self._redis.setex(
            refresh_token_key(refresh_token),
            timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            user_id,
        )
        return access_token, refresh_token

    # ── Public methods ─────────────────────────────────────────────────────────

    async def register(self, email: str, password: str) -> LoginResponse:
        """
        Register a new user account.

        Raises:
            ConflictError: If the email is already in use.

        Returns:
            LoginResponse with the new user and token pair.
        """
        existing = await self._db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            raise ConflictError(f"Email '{email}' is already registered.")

        user = User(
            email=email,
            password_hash=hash_password(password),
        )
        self._db.add(user)
        await self._db.flush()

        access_token, refresh_token = await self._issue_token_pair(user)
        logger.info("user_registered", user_id=str(user.id), email=email)
        return LoginResponse(
            user=UserResponse.model_validate(user),
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def login(self, email: str, password: str) -> LoginResponse:
        """
        Authenticate a user with email and password.

        Raises:
            UnauthorizedError: If credentials are invalid or account is inactive.

        Returns:
            LoginResponse with the user and a fresh token pair.
        """
        result = await self._db.execute(
            select(User).where(User.email == email, User.is_active.is_(True))
        )
        user = result.scalar_one_or_none()

        if user is None or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid email or password.")

        access_token, refresh_token = await self._issue_token_pair(user)
        logger.info("user_logged_in", user_id=str(user.id))
        return LoginResponse(
            user=UserResponse.model_validate(user),
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh_tokens(self, refresh_token: str) -> TokenPair:
        """
        Validate a refresh token and rotate it: revoke old, issue new pair.

        Raises:
            UnauthorizedError: If the token is invalid, expired, or revoked.

        Returns:
            New TokenPair.
        """
        try:
            payload = decode_token(refresh_token)
        except JWTError as err:
            raise UnauthorizedError("Invalid or expired refresh token.") from err

        if payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid token type.")

        rkey = refresh_token_key(refresh_token)
        stored_user_id = await self._redis.get(rkey)
        if not stored_user_id:
            raise UnauthorizedError("Refresh token has been revoked or expired.")

        result = await self._db.execute(
            select(User).where(
                User.id == uuid.UUID(stored_user_id),
                User.is_active.is_(True),
            )
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise UnauthorizedError("User not found or inactive.")

        # Rotate: delete old token, issue new pair
        await self._redis.delete(rkey)
        access_token, new_refresh = await self._issue_token_pair(user)
        logger.info("tokens_rotated", user_id=str(user.id))
        return TokenPair(access_token=access_token, refresh_token=new_refresh)

    async def logout(self, refresh_token: str) -> None:
        """
        Invalidate a refresh token by deleting it from Redis.

        Args:
            refresh_token: The refresh token string to revoke.
        """
        deleted = await self._redis.delete(refresh_token_key(refresh_token))
        if deleted:
            logger.info("user_logged_out")
