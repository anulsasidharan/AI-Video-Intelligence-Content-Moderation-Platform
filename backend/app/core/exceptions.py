from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse


class AppException(Exception):
    """Base application exception that maps to an HTTP error response."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: dict | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


# ── Common pre-built exceptions ───────────────────────────────────────────────


class NotFoundError(AppException):
    def __init__(self, resource: str, resource_id: str = "") -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=f"{resource} not found." + (f" id={resource_id}" if resource_id else ""),
        )


class UnauthorizedError(AppException):
    def __init__(self, message: str = "Authentication required.") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message=message,
        )


class ForbiddenError(AppException):
    def __init__(self, message: str = "Insufficient permissions.") -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message=message,
        )


class ConflictError(AppException):
    def __init__(self, message: str) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="CONFLICT",
            message=message,
        )


class ValidationError(AppException):
    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=message,
            details=details,
        )


class RateLimitError(AppException):
    def __init__(self, retry_after: int = 60) -> None:
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            code="RATE_LIMIT_EXCEEDED",
            message="Too many requests. Please slow down and try again later.",
            details={"retry_after_seconds": retry_after},
        )
        self.retry_after = retry_after


# ── Exception handlers ────────────────────────────────────────────────────────


def _error_envelope(code: str, message: str, details: dict) -> dict:
    return {"error": {"code": code, "message": message, "details": details}}


async def app_exception_handler(request: Request, exc: AppException) -> ORJSONResponse:
    return ORJSONResponse(
        status_code=exc.status_code,
        content=_error_envelope(exc.code, exc.message, exc.details),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> ORJSONResponse:
    details = {
        "fields": [
            {
                "loc": " -> ".join(str(part) for part in e["loc"]),
                "msg": e["msg"],
                "type": e["type"],
            }
            for e in exc.errors()
        ]
    }
    return ORJSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_error_envelope("VALIDATION_ERROR", "Request validation failed.", details),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> ORJSONResponse:
    return ORJSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_envelope(
            "INTERNAL_SERVER_ERROR",
            "An unexpected error occurred.",
            {},
        ),
    )
