import uuid
from typing import Annotated

import structlog
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_token
from app.dependencies import get_db
from app.models.user import User, UserRole

logger = structlog.get_logger(__name__)

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Validate JWT and return the authenticated User. Raises 401 if invalid."""
    if credentials is None:
        raise UnauthorizedError("Bearer token missing.")

    try:
        payload = decode_token(credentials.credentials)
    except JWTError as exc:
        raise UnauthorizedError("Invalid or expired token.") from exc

    if payload.get("type") != "access":
        raise UnauthorizedError("Invalid token type.")

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Token subject missing.")

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError as exc:
        raise UnauthorizedError("Invalid token subject.") from exc

    result = await db.execute(select(User).where(User.id == user_uuid, User.is_active.is_(True)))
    user = result.scalar_one_or_none()

    if user is None:
        raise UnauthorizedError("User not found or inactive.")

    structlog.contextvars.bind_contextvars(user_id=str(user.id), role=user.role.value)
    return user


def require_role(*roles: UserRole):
    """Returns a FastAPI dependency that asserts the current user has one of the given roles."""

    async def _check(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role not in roles:
            raise ForbiddenError(
                f"This action requires one of: {', '.join(r.value for r in roles)}."
            )
        return current_user

    return _check


# ── Typed dependency aliases ──────────────────────────────────────────────────

CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_role(UserRole.ADMIN))]
OperatorUser = Annotated[User, Depends(require_role(UserRole.ADMIN, UserRole.OPERATOR))]
