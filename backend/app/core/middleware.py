import time
import uuid

import orjson
import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.rate_limit import RateLimiter, match_tier

logger = structlog.get_logger(__name__)

_SKIP_PATHS = frozenset({"/health", "/docs", "/redoc", "/openapi.json"})


class DataWrapperMiddleware(BaseHTTPMiddleware):
    """Wrap all successful JSON responses in {\"data\": ...} envelope.

    This keeps the API response shape consistent with the frontend's
    expectation of { data: { ... } } for all 2xx responses.
    Error responses already use { error: { code, message } } and are not wrapped.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        content_type = response.headers.get("content-type", "")
        if (
            not (200 <= response.status_code < 300)
            or "application/json" not in content_type
            or request.url.path in _SKIP_PATHS
        ):
            return response

        # Consume the body
        chunks: list[bytes] = []
        async for chunk in response.body_iterator:
            chunks.append(chunk if isinstance(chunk, bytes) else chunk.encode())
        body = b"".join(chunks)

        try:
            payload = orjson.loads(body)
            # Don't double-wrap if already has data/error key
            if isinstance(payload, dict) and ("data" in payload or "error" in payload):
                return Response(
                    content=body,
                    status_code=response.status_code,
                    media_type="application/json",
                    headers=dict(response.headers),
                )
            wrapped = orjson.dumps({"data": payload})
            headers = dict(response.headers)
            headers["content-length"] = str(len(wrapped))
            return Response(
                content=wrapped,
                status_code=response.status_code,
                media_type="application/json",
                headers=headers,
            )
        except Exception:
            return Response(
                content=body,
                status_code=response.status_code,
                media_type="application/json",
                headers=dict(response.headers),
            )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Per-IP fixed-window rate limiter.

    Checks the route-specific tier AND a global per-IP ceiling.
    Returns HTTP 429 with standard Retry-After / X-RateLimit-* headers
    when either limit is exceeded.

    The middleware is a no-op when Redis is unavailable (fail-open) so
    that a Redis outage does not take down the API.
    """

    def _get_client_ip(self, request: Request) -> str:
        """Resolve the real client IP, respecting reverse-proxy headers."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        tier_name = match_tier(request.url.path, request.method)

        if tier_name is None:
            # Exempt path — skip rate limiting entirely
            return await call_next(request)

        try:
            from app.dependencies import get_redis_client

            redis_client = get_redis_client()
            limiter = RateLimiter(redis_client)
            client_ip = self._get_client_ip(request)
            result = await limiter.check_all(tier_name, client_ip)
        except Exception as exc:
            # Fail-open: Redis unavailable should not block legitimate traffic
            logger.error("rate_limit_middleware_error", error=str(exc))
            return await call_next(request)

        if not result.allowed:
            content = orjson.dumps(
                {
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please slow down and try again later.",
                        "details": {"retry_after_seconds": result.retry_after},
                    }
                }
            )
            headers = {
                "Content-Type": "application/json",
                "Retry-After": str(result.retry_after),
                "X-RateLimit-Limit": str(result.limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(result.reset_at),
            }
            return Response(content=content, status_code=429, headers=headers)

        response = await call_next(request)

        # Append rate limit headers on allowed responses too (for client awareness)
        response.headers["X-RateLimit-Limit"] = str(result.limit)
        response.headers["X-RateLimit-Remaining"] = str(result.remaining)
        response.headers["X-RateLimit-Reset"] = str(result.reset_at)
        return response


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attaches a unique request_id to every request and logs method/path/status/duration."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        start = time.perf_counter()
        response: Response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        logger.info(
            "http_request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        response.headers["X-Request-ID"] = request_id
        return response
