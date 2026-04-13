import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

import redis.asyncio as aioredis
import structlog
from fastapi import APIRouter, Depends, Request, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.config import settings
from app.core.exceptions import ConflictError, ForbiddenError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    refresh_token_key,
    verify_password,
)
from app.dependencies import get_db, get_redis
from app.models.audit import AccessAuditLog, AuditAction, AuditStatus
from app.models.password_reset import PasswordResetToken
from app.models.user import User, UserRole
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenPair,
)
from app.schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])
logger = structlog.get_logger(__name__)


# ── Audit helper ──────────────────────────────────────────────────────────────


def _get_client_ip(request: Request) -> str | None:
    """Return the real client IP, respecting X-Forwarded-For from proxies."""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


async def _log_access(
    db: AsyncSession,
    *,
    action: AuditAction,
    status: AuditStatus,
    email: str,
    request: Request,
    user: User | None = None,
    failure_reason: str | None = None,
) -> None:
    log = AccessAuditLog(
        user_id=user.id if user else None,
        email=email,
        username=user.name if user else None,
        action=action,
        status=status,
        failure_reason=failure_reason,
        ip_address=_get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.add(log)


async def _log_access_and_commit(
    db: AsyncSession,
    *,
    action: AuditAction,
    status: AuditStatus,
    email: str,
    request: Request,
    user: User | None = None,
    failure_reason: str | None = None,
) -> None:
    """
    Persist an access audit row and commit immediately.

    Used when the handler will raise afterward: ``get_db`` rolls back the
    session on exceptions, which would otherwise discard a mere flush().
    """
    await _log_access(
        db,
        action=action,
        status=status,
        email=email,
        request=request,
        user=user,
        failure_reason=failure_reason,
    )
    await db.commit()


# ── POST /auth/register ───────────────────────────────────────────────────────


@router.post(
    "/register",
    response_model=LoginResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    body: RegisterRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
) -> LoginResponse:
    existing_result = await db.execute(select(User).where(User.email == body.email))
    existing = existing_result.scalar_one_or_none()
    if existing is not None:
        if existing.is_blocked:
            raise ForbiddenError(
                "This email address has been permanently blocked and cannot be used to register."
            )
        raise ConflictError(f"Email '{body.email}' is already registered.")

    user = User(
        email=body.email,
        name=body.name,
        password_hash=hash_password(body.password),
        role=UserRole.OPERATOR,
        whatsapp_number=body.whatsapp_number,
    )
    db.add(user)
    await db.flush()

    from app.services.billing_service import ensure_default_subscription

    await ensure_default_subscription(db, user.id)

    user_id = str(user.id)
    access_token = create_access_token(user_id, extra={"role": user.role.value})
    refresh_token = create_refresh_token(user_id)

    await redis.setex(
        refresh_token_key(refresh_token),
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        user_id,
    )

    logger.info("user_registered", user_id=user_id, email=user.email)

    # Welcome notifications — email always; WhatsApp if number provided
    from app.services.notification_dispatcher import dispatch_async

    channels = ["email", "in_app"]
    if user.whatsapp_number:
        channels.append("whatsapp")
    await dispatch_async(
        db=db,
        user=user,
        channels=channels,
        event_type="user.registered",
        title="Welcome to VidShield AI",
        message=(
            f"Hi {user.name or user.email}, your account has been created successfully. "
            "Start uploading videos for AI-powered content moderation."
        ),
        priority="medium",
        extra={"user_name": user.name or user.email},
    )

    return LoginResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
        refresh_token=refresh_token,
    )


# ── POST /auth/login ──────────────────────────────────────────────────────────


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Authenticate and receive JWT tokens",
)
async def login(
    body: LoginRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
) -> LoginResponse:
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    # Wrong password or unknown email — commit audit before raise (get_db rolls back on error)
    if user is None:
        await _log_access_and_commit(
            db,
            action=AuditAction.LOGIN,
            status=AuditStatus.FAILURE,
            email=body.email,
            request=request,
            failure_reason="user_not_found",
        )
        raise UnauthorizedError("Invalid email or password.")

    if not verify_password(body.password, user.password_hash):
        await _log_access_and_commit(
            db,
            action=AuditAction.LOGIN,
            status=AuditStatus.FAILURE,
            email=body.email,
            request=request,
            user=user,
            failure_reason="invalid_password",
        )
        raise UnauthorizedError("Invalid email or password.")

    if user.is_blocked:
        await _log_access_and_commit(
            db,
            action=AuditAction.LOGIN,
            status=AuditStatus.FAILURE,
            email=body.email,
            request=request,
            user=user,
            failure_reason="account_blocked",
        )
        raise ForbiddenError("Your account has been permanently blocked. Contact an administrator.")

    if not user.is_active:
        await _log_access_and_commit(
            db,
            action=AuditAction.LOGIN,
            status=AuditStatus.FAILURE,
            email=body.email,
            request=request,
            user=user,
            failure_reason="account_suspended",
        )
        raise ForbiddenError("Your account has been suspended. Contact an administrator.")

    # Success
    user_id = str(user.id)
    access_token = create_access_token(user_id, extra={"role": user.role.value})
    refresh_token = create_refresh_token(user_id)

    await redis.setex(
        refresh_token_key(refresh_token),
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        user_id,
    )

    await _log_access(
        db,
        action=AuditAction.LOGIN,
        status=AuditStatus.SUCCESS,
        email=body.email,
        request=request,
        user=user,
    )

    logger.info("user_logged_in", user_id=user_id)
    return LoginResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
        refresh_token=refresh_token,
    )


# ── POST /auth/refresh ────────────────────────────────────────────────────────


@router.post(
    "/refresh",
    response_model=TokenPair,
    summary="Rotate access token using a valid refresh token",
)
async def refresh(
    body: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
) -> TokenPair:
    try:
        payload = decode_token(body.refresh_token)
    except JWTError as exc:
        raise UnauthorizedError("Invalid or expired refresh token.") from exc

    if payload.get("type") != "refresh":
        raise UnauthorizedError("Invalid token type.")

    rkey = refresh_token_key(body.refresh_token)
    stored_user_id = await redis.get(rkey)
    if not stored_user_id:
        raise UnauthorizedError("Refresh token has been revoked or expired.")

    result = await db.execute(
        select(User).where(User.id == uuid.UUID(stored_user_id), User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise UnauthorizedError("User not found or inactive.")

    await redis.delete(rkey)
    user_id = str(user.id)
    new_access = create_access_token(user_id, extra={"role": user.role.value})
    new_refresh = create_refresh_token(user_id)

    await redis.setex(
        refresh_token_key(new_refresh),
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        user_id,
    )

    logger.info("tokens_rotated", user_id=user_id)
    return TokenPair(access_token=new_access, refresh_token=new_refresh)


# ── POST /auth/logout ─────────────────────────────────────────────────────────


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Invalidate the current refresh token",
)
async def logout(
    body: RefreshRequest,
    request: Request,
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
) -> MessageResponse:
    deleted = await redis.delete(refresh_token_key(body.refresh_token))
    if deleted:
        await _log_access(
            db,
            action=AuditAction.LOGOUT,
            status=AuditStatus.SUCCESS,
            email=current_user.email,
            request=request,
            user=current_user,
        )
        logger.info("user_logged_out", user_id=str(current_user.id))
    return MessageResponse(message="Logged out successfully.")


# ── GET /auth/me ──────────────────────────────────────────────────────────────


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Return the currently authenticated user",
)
async def me(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user)


# ── POST /auth/forgot-password ────────────────────────────────────────────────

_RATE_LIMIT_WINDOW = 900  # 15 minutes in seconds
_RATE_LIMIT_PREFIX = "pwd_reset_rl:"


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Request a password reset email",
)
async def forgot_password(
    body: ForgotPasswordRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
) -> MessageResponse:
    """
    Send a password reset link to the given email address.

    Always returns HTTP 200 with the same message regardless of whether the
    email exists, to prevent user enumeration.

    Rate limited: max 3 requests per email per 15 minutes.
    """
    # Normalise email for the rate-limit key (avoid leaking raw email into Redis)
    email_key = hashlib.sha256(body.email.lower().encode()).hexdigest()
    rl_key = f"{_RATE_LIMIT_PREFIX}{email_key}"

    count = await redis.incr(rl_key)
    if count == 1:
        await redis.expire(rl_key, _RATE_LIMIT_WINDOW)
    if count > settings.PASSWORD_RESET_RATE_LIMIT:
        logger.warning("forgot_password_rate_limited", email_hash=email_key)
        # Return the same generic message — never expose rate-limit details
        return MessageResponse(
            message="If an account with that email exists, a reset link has been sent."
        )

    # Look up user — do NOT reveal whether email exists in any error response
    result = await db.execute(select(User).where(User.email == body.email.lower()))
    user = result.scalar_one_or_none()

    if user and user.is_active and not user.is_blocked:
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        expires_at = datetime.now(UTC) + timedelta(
            minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
        )

        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=_get_client_ip(request),
        )
        db.add(reset_token)
        await db.flush()

        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={raw_token}"

        try:
            from app.services.email_service import EmailService

            EmailService().send_password_reset(
                to_email=user.email,
                user_name=user.name or user.email,
                reset_url=reset_url,
                expires_minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES,
            )
        except Exception as exc:
            logger.error("forgot_password_email_failed", user_id=str(user.id), error=str(exc))

        logger.info("forgot_password_token_issued", user_id=str(user.id))

    return MessageResponse(
        message="If an account with that email exists, a reset link has been sent."
    )


# ── POST /auth/reset-password ─────────────────────────────────────────────────


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset password using a valid reset token",
)
async def reset_password(
    body: ResetPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    """
    Validate the reset token and update the user's password.

    Tokens are single-use and expire after PASSWORD_RESET_TOKEN_EXPIRE_MINUTES.
    """
    token_hash = hashlib.sha256(body.token.encode()).hexdigest()

    result = await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    )
    reset_token = result.scalar_one_or_none()

    if reset_token is None:
        raise UnauthorizedError("Invalid or expired password reset token.")

    if reset_token.used_at is not None:
        raise UnauthorizedError("This password reset link has already been used.")

    if reset_token.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
        raise UnauthorizedError("This password reset link has expired. Please request a new one.")

    user_result = await db.execute(
        select(User).where(User.id == reset_token.user_id, User.is_active.is_(True))
    )
    user = user_result.scalar_one_or_none()
    if user is None or user.is_blocked:
        raise UnauthorizedError("Invalid or expired password reset token.")

    # Update password
    user.password_hash = hash_password(body.new_password)

    # Mark token as used (one-time use)
    reset_token.used_at = datetime.now(UTC)

    await db.flush()

    logger.info("password_reset_success", user_id=str(user.id))

    # Send confirmation email (non-fatal)
    try:
        from app.services.email_service import EmailService

        EmailService().send_password_reset_confirmation(
            to_email=user.email,
            user_name=user.name or user.email,
        )
    except Exception as exc:
        logger.error(
            "reset_password_confirmation_email_failed",
            user_id=str(user.id),
            error=str(exc),
        )

    return MessageResponse(message="Your password has been reset successfully. You can now log in.")
