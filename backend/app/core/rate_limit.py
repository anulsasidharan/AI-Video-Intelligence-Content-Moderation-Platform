"""
R-01 Redis-based Fixed-Window Rate Limiter

Architecture
────────────
Each request is matched against an ordered list of route tiers.
The first matching tier wins.  A global per-IP catch-all tier runs for
every request in addition to the route-specific tier (whichever is stricter).

Redis key schema
────────────────
    rl:{tier_name}:{identifier}:{window_bucket}

  tier_name      — e.g. "auth", "upload", "api_write", "global"
  identifier     — SHA-256 of the client IP (to avoid storing raw IPs in Redis)
  window_bucket  — floor(unix_time / window_seconds)  — rotates automatically

Key TTL is set to window_seconds * 2, so exhausted buckets expire without
a separate cleanup job.

Usage
─────
    from app.core.rate_limit import RateLimiter, TIERS, match_tier
    limiter = RateLimiter(redis_client)
    result  = await limiter.check("auth", client_ip)
    if not result.allowed:
        raise RateLimitError(retry_after=result.retry_after)
"""

from __future__ import annotations

import hashlib
import math
import time
from dataclasses import dataclass
from typing import NamedTuple

import redis.asyncio as aioredis
import structlog

logger = structlog.get_logger(__name__)


# ── Tier definitions ───────────────────────────────────────────────────────────


class Tier(NamedTuple):
    name: str
    requests: int  # max requests in the window
    window: int  # window length in seconds


# Route → tier mapping (checked in order; first match wins).
# Each entry is (path_prefix, http_methods_or_None, tier).
# None for methods means "any method".

TIERS: dict[str, Tier] = {
    # Auth endpoints — tight limits to slow brute-force; 20/min per real IP is
    # enough for legitimate users while still blocking credential-stuffing.
    "auth": Tier("auth", requests=20, window=60),
    # Sensitive single-use flows
    "sensitive": Tier("sensitive", requests=10, window=60),
    # Heavy write operations (video upload, report generation)
    "upload": Tier("upload", requests=15, window=60),
    # Mutating API calls (POST/PUT/PATCH/DELETE outside auth)
    "api_write": Tier("api_write", requests=60, window=60),
    # Read-only API calls
    "api_read": Tier("api_read", requests=300, window=60),
    # Global per-IP safety net applied to every request
    "global": Tier("global", requests=600, window=60),
}

# Ordered rules: (path_startswith, frozenset_of_methods_or_None, tier_name)
_ROUTE_RULES: list[tuple[str, frozenset[str] | None, str]] = [
    ("/api/v1/auth/login", None, "auth"),
    ("/api/v1/auth/register", None, "auth"),
    ("/api/v1/auth/forgot-password", None, "sensitive"),
    ("/api/v1/auth/reset-password", None, "sensitive"),
    ("/api/v1/videos", frozenset({"POST"}), "upload"),
    ("/api/v1/reports", frozenset({"POST"}), "upload"),
    # All other mutating methods
    ("/api/v1/", frozenset({"POST", "PUT", "PATCH", "DELETE"}), "api_write"),
    # All remaining API reads
    ("/api/v1/", None, "api_read"),
]

# Paths that are completely exempt from rate limiting
_EXEMPT_PATHS: frozenset[str] = frozenset(
    {
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/socket.io",
    }
)


def match_tier(path: str, method: str) -> str | None:
    """
    Return the tier name for the given path + method, or None if exempt.
    """
    for exempt in _EXEMPT_PATHS:
        if path.startswith(exempt):
            return None

    for prefix, methods, tier_name in _ROUTE_RULES:
        if path.startswith(prefix) and (methods is None or method.upper() in methods):
            return tier_name

    return "api_read"  # fallback for any unmatched path


def _ip_key(ip: str) -> str:
    """Hash the raw IP so we never store PII in Redis keys."""
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


# ── Result dataclass ───────────────────────────────────────────────────────────


@dataclass(slots=True)
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    reset_at: int  # Unix timestamp when the window resets
    retry_after: int  # seconds to wait on 429

    @property
    def headers(self) -> dict[str, str]:
        return {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(self.remaining),
            "X-RateLimit-Reset": str(self.reset_at),
            **({"Retry-After": str(self.retry_after)} if not self.allowed else {}),
        }


# ── Core limiter ───────────────────────────────────────────────────────────────


class RateLimiter:
    """
    Fixed-window rate limiter backed by Redis.

    Thread/coroutine-safe because Redis INCR is atomic.
    Uses a pipeline (one round-trip) per check.
    """

    def __init__(self, redis: aioredis.Redis) -> None:
        self._redis = redis

    async def check(self, tier_name: str, client_ip: str) -> RateLimitResult:
        """
        Increment the counter for (tier, ip) and return the result.

        Always increments — the caller must check result.allowed before
        continuing.
        """
        tier = TIERS[tier_name]
        bucket = math.floor(time.time() / tier.window)
        key = f"rl:{tier_name}:{_ip_key(client_ip)}:{bucket}"
        ttl_safety = tier.window * 2  # keep key alive across two windows

        pipe = self._redis.pipeline(transaction=False)
        pipe.incr(key)
        pipe.ttl(key)
        results = await pipe.execute()
        count: int = results[0]
        ttl: int = results[1]

        # Set TTL on first increment (INCR creates the key if absent)
        if count == 1 or ttl < 0:
            await self._redis.expire(key, ttl_safety)
            ttl = ttl_safety

        reset_at = int(time.time()) + ttl
        remaining = max(0, tier.requests - count)
        allowed = count <= tier.requests
        retry_after = ttl if not allowed else 0

        if not allowed:
            logger.warning(
                "rate_limit_exceeded",
                tier=tier_name,
                ip_hash=_ip_key(client_ip),
                count=count,
                limit=tier.requests,
            )

        return RateLimitResult(
            allowed=allowed,
            limit=tier.requests,
            remaining=remaining,
            reset_at=reset_at,
            retry_after=retry_after,
        )

    async def check_all(self, tier_name: str, client_ip: str) -> RateLimitResult:
        """
        Check both the route-specific tier AND the global per-IP tier.
        Returns the more restrictive result (whichever denies first).
        """
        route_result = await self.check(tier_name, client_ip)
        global_result = await self.check("global", client_ip)

        if not route_result.allowed:
            return route_result
        if not global_result.allowed:
            return global_result
        # Both allowed — return route result (more specific headers)
        return route_result
