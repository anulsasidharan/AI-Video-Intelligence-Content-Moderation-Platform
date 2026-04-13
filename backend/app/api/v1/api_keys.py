"""
API Keys — CRUD for user-owned programmatic access keys.

All endpoints require a valid JWT Bearer token (portal session).
The raw key is returned only on creation and never stored in plaintext.
"""

import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.dependencies import get_db
from app.models.api_key import ApiKey
from app.schemas.api_key import (
    ApiKeyCreate,
    ApiKeyCreateResponse,
    ApiKeyListResponse,
    ApiKeyRename,
    ApiKeyResponse,
)

router = APIRouter(prefix="/api-keys", tags=["api-keys"])
logger = structlog.get_logger(__name__)

_MAX_KEYS_PER_USER = 20


def _to_response(key: ApiKey) -> ApiKeyResponse:
    return ApiKeyResponse(
        id=key.id,
        name=key.name,
        masked=key.masked,
        created_at=key.created_at,
        last_used_at=key.last_used_at,
        request_count=key.request_count,
        status="revoked" if key.is_revoked else "active",
    )


# ── GET /api-keys ─────────────────────────────────────────────────────────────


@router.get("", response_model=ApiKeyListResponse, summary="List API keys for the current user")
async def list_api_keys(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiKeyListResponse:
    q = select(ApiKey).where(ApiKey.user_id == current_user.id).order_by(ApiKey.created_at.desc())
    total = await db.scalar(select(func.count()).select_from(q.subquery())) or 0
    result = await db.execute(q)
    keys = result.scalars().all()
    return ApiKeyListResponse(items=[_to_response(k) for k in keys], total=total)


# ── POST /api-keys ────────────────────────────────────────────────────────────


@router.post(
    "",
    response_model=ApiKeyCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a new API key",
)
async def create_api_key(
    body: ApiKeyCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiKeyCreateResponse:
    """
    Generates a new API key.  The full key is returned exactly once — it is
    not stored and cannot be retrieved again.
    """
    active_count = (
        await db.scalar(
            select(func.count()).where(
                ApiKey.user_id == current_user.id,
                ApiKey.is_revoked.is_(False),
            )
        )
        or 0
    )

    if active_count >= _MAX_KEYS_PER_USER:
        raise ValidationError(
            f"Maximum of {_MAX_KEYS_PER_USER} active API keys per user reached. "
            "Revoke an existing key before creating a new one."
        )

    raw_key, key_hash, masked = ApiKey.generate()

    key = ApiKey(
        user_id=current_user.id,
        name=body.name,
        key_hash=key_hash,
        masked=masked,
    )
    db.add(key)
    await db.flush()

    logger.info("api_key_created", key_id=str(key.id), user_id=str(current_user.id))

    return ApiKeyCreateResponse(
        id=key.id,
        name=key.name,
        key=raw_key,
        masked=key.masked,
        created_at=key.created_at,
    )


# ── PATCH /api-keys/{id} ──────────────────────────────────────────────────────


@router.patch("/{key_id}", response_model=ApiKeyResponse, summary="Rename an API key")
async def rename_api_key(
    key_id: uuid.UUID,
    body: ApiKeyRename,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiKeyResponse:
    result = await db.execute(select(ApiKey).where(ApiKey.id == key_id))
    key = result.scalar_one_or_none()
    if not key:
        raise NotFoundError("ApiKey", str(key_id))
    if key.user_id != current_user.id:
        raise ForbiddenError("You do not own this API key.")

    key.name = body.name
    logger.info("api_key_renamed", key_id=str(key_id), user_id=str(current_user.id))
    return _to_response(key)


# ── DELETE /api-keys/{id} ─────────────────────────────────────────────────────


@router.delete(
    "/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Revoke and delete an API key",
)
async def revoke_api_key(
    key_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    result = await db.execute(select(ApiKey).where(ApiKey.id == key_id))
    key = result.scalar_one_or_none()
    if not key:
        raise NotFoundError("ApiKey", str(key_id))
    if key.user_id != current_user.id:
        raise ForbiddenError("You do not own this API key.")

    await db.delete(key)
    logger.info("api_key_revoked", key_id=str(key_id), user_id=str(current_user.id))
