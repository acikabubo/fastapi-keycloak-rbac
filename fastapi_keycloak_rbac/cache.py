"""
Redis token cache for fastapi-keycloak-rbac.

Provides TokenCache for caching decoded JWT claims in Redis to reduce
repeated Keycloak validation calls. Requires the ``redis`` optional extra:

    pip install fastapi-keycloak-rbac[redis]

All operations are fail-open: if Redis is unavailable, the error is logged
and the caller receives None (cache miss), allowing authentication to proceed
normally against Keycloak.

Example::

    from fastapi_keycloak_rbac.cache import TokenCache

    cache = TokenCache(redis_url="redis://localhost:6379/1")
    claims = await cache.get_cached_claims(token)
    if claims is None:
        claims = await manager.decode_token(token)
        await cache.set_cached_claims(token, claims)
"""

import hashlib
import json
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

_CACHE_KEY_PREFIX = "token:claims:"
_MIN_TTL = 1  # seconds


def _token_hash(token: str) -> str:
    """Return SHA-256 hex digest of the token (never store raw tokens)."""
    return hashlib.sha256(token.encode()).hexdigest()


def _cache_key(token: str) -> str:
    return f"{_CACHE_KEY_PREFIX}{_token_hash(token)}"


class TokenCache:
    """
    Redis-backed cache for decoded JWT token claims.

    Stores token claims keyed by a SHA-256 hash of the raw token string.
    TTL is automatically derived from the token's ``exp`` claim minus a
    configurable buffer to avoid serving stale claims near expiry.

    All Redis errors are caught and logged; the cache degrades gracefully
    to a no-op (fail-open behaviour).

    Args:
        redis_url: Redis connection URL (e.g. ``redis://localhost:6379/1``).
        ttl_buffer: Seconds to subtract from token expiry when computing TTL.
                    Defaults to 30.

    Example::

        cache = TokenCache(redis_url="redis://localhost:6379/1", ttl_buffer=30)
        claims = await cache.get_cached_claims(token)
    """

    def __init__(self, redis_url: str, ttl_buffer: int = 30) -> None:
        try:
            from redis.asyncio import Redis
        except ImportError as exc:
            raise ImportError(
                "Redis support requires the 'redis' extra: "
                "pip install fastapi-keycloak-rbac[redis]"
            ) from exc

        self._redis: Any = Redis.from_url(redis_url, decode_responses=True)
        self._ttl_buffer = ttl_buffer
        logger.info("TokenCache initialized (url=%s)", redis_url)

    async def get_cached_claims(self, token: str) -> dict[str, Any] | None:
        """
        Retrieve cached token claims from Redis.

        Args:
            token: Raw JWT access token string.

        Returns:
            Decoded claims dict on cache hit, ``None`` on miss or error.
        """
        try:
            key = _cache_key(token)
            raw = await self._redis.get(key)
            if raw is None:
                logger.debug("Token cache miss")
                return None
            logger.debug("Token cache hit")
            result: dict[str, Any] = json.loads(raw)
            return result
        except Exception as exc:
            logger.warning("Redis get error (fail-open): %s", exc)
            return None

    async def set_cached_claims(
        self, token: str, claims: dict[str, Any]
    ) -> None:
        """
        Store token claims in Redis with an automatic TTL.

        TTL is computed as ``claims["exp"] - now - ttl_buffer``, floored at
        ``_MIN_TTL`` seconds. If ``exp`` is missing the entry is not cached.

        Args:
            token: Raw JWT access token string.
            claims: Decoded token claims dict (must contain ``exp`` key).
        """
        try:
            exp = claims.get("exp")
            if exp is None:
                logger.debug("Token has no exp claim, skipping cache")
                return
            ttl = max(int(exp - time.time()) - self._ttl_buffer, _MIN_TTL)
            key = _cache_key(token)
            await self._redis.setex(key, ttl, json.dumps(claims))
            logger.debug("Token claims cached (ttl=%ds)", ttl)
        except Exception as exc:
            logger.warning("Redis set error (fail-open): %s", exc)

    async def invalidate_token(self, token: str) -> None:
        """
        Remove a token's cached claims from Redis.

        Args:
            token: Raw JWT access token string to invalidate.
        """
        try:
            key = _cache_key(token)
            await self._redis.delete(key)
            logger.debug("Token cache entry invalidated")
        except Exception as exc:
            logger.warning("Redis delete error (fail-open): %s", exc)

    async def close(self) -> None:
        """Close the underlying Redis connection."""
        try:
            await self._redis.aclose()
        except Exception as exc:
            logger.warning("Redis close error: %s", exc)
