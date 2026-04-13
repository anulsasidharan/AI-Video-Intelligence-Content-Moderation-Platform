"""
Policies API — B-06
CRUD for content moderation rule sets.

Permission model
────────────────
Default policies  (is_default=True, created by admin)
  • Visible to every authenticated user.
  • Any operator can toggle is_active   → PATCH /{id}/toggle
  • Full edits (name/rules/etc.)        → admin only  (PUT /{id})
  • Delete                              → forbidden for everyone

Custom policies  (is_default=False, created by individual users)
  • Visible to their owner only.
  • Owner has full CRUD.

Fallback: when a user has no active custom policy the AI pipeline
falls back to the active default policies.
"""

import uuid
from typing import Annotated

import redis.asyncio as aioredis
import structlog
from fastapi import APIRouter, Depends, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, OperatorUser
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.dependencies import get_db, get_redis
from app.models.policy import Policy
from app.models.user import UserRole
from app.schemas.policy import (
    PolicyCreate,
    PolicyListResponse,
    PolicyResponse,
    PolicyUpdate,
)

router = APIRouter(prefix="/policies", tags=["policies"])
logger = structlog.get_logger(__name__)


def _policy_cache_key(tenant_id: str | None) -> str:
    return f"policy:{tenant_id or 'global'}:active"


async def _active_policy_count(db: AsyncSession, user_id: uuid.UUID) -> int:
    """Return the number of active policies visible to a user (defaults + their own)."""
    result = await db.scalar(
        select(func.count()).where(
            Policy.is_active.is_(True),
            or_(Policy.is_default.is_(True), Policy.owner_id == user_id),
        )
    )
    return result or 0


# ── GET /policies ──────────────────────────────────────────────────────────────


@router.get(
    "",
    response_model=PolicyListResponse,
    summary="List policies visible to the current user",
)
async def list_policies(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PolicyListResponse:
    """
    Returns:
    - All default policies (is_default=True) — visible to every user.
    - All custom policies owned by the requesting user.

    Ordered: defaults first, then custom newest-first.
    """
    q = select(Policy).where(or_(Policy.is_default.is_(True), Policy.owner_id == current_user.id))
    if current_user.tenant_id:
        q = q.where(
            or_(
                Policy.tenant_id == current_user.tenant_id,
                Policy.is_default.is_(True),
            )
        )

    total = await db.scalar(select(func.count()).select_from(q.subquery())) or 0
    result = await db.execute(q.order_by(Policy.is_default.desc(), Policy.created_at.desc()))
    policies = result.scalars().all()

    return PolicyListResponse(
        items=[PolicyResponse.model_validate(p) for p in policies],
        total=total,
    )


# ── POST /policies ─────────────────────────────────────────────────────────────


@router.post(
    "",
    response_model=PolicyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new moderation policy",
)
async def create_policy(
    body: PolicyCreate,
    current_user: OperatorUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
) -> PolicyResponse:
    """Any operator can create a custom policy. Only admins can set is_default=True."""
    if body.is_default and current_user.role != UserRole.ADMIN:
        raise ForbiddenError("Only admins can create default policies.")

    rules_data = [r.model_dump() for r in body.rules] if body.rules else None
    policy = Policy(
        name=body.name,
        description=body.description,
        is_active=body.is_active,
        is_default=body.is_default,
        rules=rules_data,
        default_action=body.default_action,
        owner_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )
    db.add(policy)
    await db.flush()

    await redis.delete(_policy_cache_key(current_user.tenant_id))
    logger.info("policy_created", policy_id=str(policy.id), is_default=policy.is_default)
    return PolicyResponse.model_validate(policy)


# ── GET /policies/{id} ─────────────────────────────────────────────────────────


@router.get("/{policy_id}", response_model=PolicyResponse, summary="Get policy detail")
async def get_policy(
    policy_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PolicyResponse:
    result = await db.execute(select(Policy).where(Policy.id == policy_id))
    policy = result.scalar_one_or_none()
    if not policy:
        raise NotFoundError("Policy", str(policy_id))
    if not policy.is_default and policy.owner_id != current_user.id:
        raise ForbiddenError("You do not have access to this policy.")
    return PolicyResponse.model_validate(policy)


# ── PATCH /policies/{id}/toggle ────────────────────────────────────────────────


@router.patch(
    "/{policy_id}/toggle",
    response_model=PolicyResponse,
    summary="Toggle a policy's active state",
)
async def toggle_policy(
    policy_id: uuid.UUID,
    current_user: OperatorUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
) -> PolicyResponse:
    """
    Flips is_active on the policy.
    - Default policies: any operator may toggle.
    - Custom policies: owner only.
    """
    result = await db.execute(select(Policy).where(Policy.id == policy_id))
    policy = result.scalar_one_or_none()
    if not policy:
        raise NotFoundError("Policy", str(policy_id))

    if not policy.is_default and policy.owner_id != current_user.id:
        raise ForbiddenError("You can only toggle your own policies.")

    # Prevent disabling the last active policy
    if policy.is_active:
        active_count = await _active_policy_count(db, current_user.id)
        if active_count <= 1:
            raise ValidationError(
                "At least one policy must remain active. "
                "Enable another policy before disabling this one."
            )

    policy.is_active = not policy.is_active
    await redis.delete(_policy_cache_key(current_user.tenant_id))
    logger.info("policy_toggled", policy_id=str(policy_id), is_active=policy.is_active)
    return PolicyResponse.model_validate(policy)


# ── PUT /policies/{id} ─────────────────────────────────────────────────────────


@router.put("/{policy_id}", response_model=PolicyResponse, summary="Update a moderation policy")
async def update_policy(
    policy_id: uuid.UUID,
    body: PolicyUpdate,
    current_user: OperatorUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
) -> PolicyResponse:
    """
    Full field update.
    - Default policies: admin only (for is_active use /toggle instead).
    - Custom policies: owner only.
    """
    result = await db.execute(select(Policy).where(Policy.id == policy_id))
    policy = result.scalar_one_or_none()
    if not policy:
        raise NotFoundError("Policy", str(policy_id))

    if policy.is_default and current_user.role != UserRole.ADMIN:
        raise ForbiddenError(
            "Only admins can edit default policies. Use the toggle to enable/disable."
        )
    if not policy.is_default and policy.owner_id != current_user.id:
        raise ForbiddenError("You can only edit your own policies.")

    # Prevent disabling the last active policy via full update
    if body.is_active is False and policy.is_active:
        active_count = await _active_policy_count(db, current_user.id)
        if active_count <= 1:
            raise ValidationError(
                "At least one policy must remain active. "
                "Enable another policy before disabling this one."
            )

    if body.name is not None:
        policy.name = body.name
    if body.description is not None:
        policy.description = body.description
    if body.is_active is not None:
        policy.is_active = body.is_active
    if body.is_default is not None:
        policy.is_default = body.is_default
    if body.rules is not None:
        policy.rules = [r.model_dump() for r in body.rules]
    if body.default_action is not None:
        policy.default_action = body.default_action

    await redis.delete(_policy_cache_key(current_user.tenant_id))
    logger.info("policy_updated", policy_id=str(policy_id))
    return PolicyResponse.model_validate(policy)


# ── DELETE /policies/{id} ──────────────────────────────────────────────────────


@router.delete(
    "/{policy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Delete a custom policy (default policies cannot be deleted)",
)
async def delete_policy(
    policy_id: uuid.UUID,
    current_user: OperatorUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
) -> None:
    """
    Default policies cannot be deleted by anyone.
    Custom policies can only be deleted by their owner.
    """
    result = await db.execute(select(Policy).where(Policy.id == policy_id))
    policy = result.scalar_one_or_none()
    if not policy:
        raise NotFoundError("Policy", str(policy_id))

    if policy.is_default:
        raise ForbiddenError("Default policies cannot be deleted.")
    if policy.owner_id != current_user.id:
        raise ForbiddenError("You can only delete your own policies.")

    await db.delete(policy)
    await redis.delete(_policy_cache_key(current_user.tenant_id))
    logger.info("policy_deleted", policy_id=str(policy_id))
