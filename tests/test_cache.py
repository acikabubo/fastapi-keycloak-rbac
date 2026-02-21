"""Tests for fastapi_keycloak_rbac/cache.py"""

import time
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from fastapi_keycloak_rbac.cache import TokenCache, _cache_key, _token_hash

SAMPLE_CLAIMS: dict[str, Any] = {
    "sub": "user-uuid-123",
    "exp": int(time.time()) + 3600,
    "preferred_username": "testuser",
}


@pytest.fixture
async def cache() -> TokenCache:
    """Return a TokenCache backed by fakeredis."""
    import fakeredis.aioredis  # type: ignore[import-untyped]

    fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    c = TokenCache.__new__(TokenCache)
    c._redis = fake_redis
    c._ttl_buffer = 30
    return c


class TestTokenHash:
    def test_returns_hex_string(self) -> None:
        h = _token_hash("mytoken")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_same_token_same_hash(self) -> None:
        assert _token_hash("tok") == _token_hash("tok")

    def test_different_tokens_different_hashes(self) -> None:
        assert _token_hash("tok1") != _token_hash("tok2")

    def test_cache_key_has_prefix(self) -> None:
        key = _cache_key("mytoken")
        assert key.startswith("token:claims:")


class TestGetCachedClaims:
    @pytest.mark.asyncio
    async def test_returns_none_on_miss(self, cache: TokenCache) -> None:
        result = await cache.get_cached_claims("nonexistent-token")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_claims_on_hit(self, cache: TokenCache) -> None:
        await cache.set_cached_claims("mytoken", SAMPLE_CLAIMS)
        result = await cache.get_cached_claims("mytoken")
        assert result == SAMPLE_CLAIMS

    @pytest.mark.asyncio
    async def test_fail_open_on_redis_error(self, cache: TokenCache) -> None:
        cache._redis.get = AsyncMock(side_effect=ConnectionError("redis down"))
        result = await cache.get_cached_claims("mytoken")
        assert result is None  # no exception raised


class TestSetCachedClaims:
    @pytest.mark.asyncio
    async def test_stores_and_retrieves(self, cache: TokenCache) -> None:
        await cache.set_cached_claims("tok", SAMPLE_CLAIMS)
        result = await cache.get_cached_claims("tok")
        assert result is not None
        assert result["sub"] == SAMPLE_CLAIMS["sub"]

    @pytest.mark.asyncio
    async def test_skips_when_no_exp(self, cache: TokenCache) -> None:
        claims_no_exp = {"sub": "user", "preferred_username": "u"}
        await cache.set_cached_claims("tok", claims_no_exp)
        result = await cache.get_cached_claims("tok")
        assert result is None  # nothing was stored

    @pytest.mark.asyncio
    async def test_ttl_is_positive(self, cache: TokenCache) -> None:
        # exp = now + 3600, buffer = 30 → TTL should be ~3570
        await cache.set_cached_claims("tok", SAMPLE_CLAIMS)
        ttl = await cache._redis.ttl(_cache_key("tok"))
        assert ttl > 0
        assert ttl <= 3600

    @pytest.mark.asyncio
    async def test_fail_open_on_redis_error(self, cache: TokenCache) -> None:
        cache._redis.setex = AsyncMock(side_effect=ConnectionError("redis down"))
        # Should not raise
        await cache.set_cached_claims("tok", SAMPLE_CLAIMS)


class TestInvalidateToken:
    @pytest.mark.asyncio
    async def test_removes_cached_entry(self, cache: TokenCache) -> None:
        await cache.set_cached_claims("tok", SAMPLE_CLAIMS)
        await cache.invalidate_token("tok")
        result = await cache.get_cached_claims("tok")
        assert result is None

    @pytest.mark.asyncio
    async def test_no_error_on_missing_key(self, cache: TokenCache) -> None:
        # Should not raise even if key doesn't exist
        await cache.invalidate_token("nonexistent")

    @pytest.mark.asyncio
    async def test_fail_open_on_redis_error(self, cache: TokenCache) -> None:
        cache._redis.delete = AsyncMock(side_effect=ConnectionError("redis down"))
        await cache.invalidate_token("tok")  # no exception


class TestImportError:
    def test_raises_import_error_without_redis(self) -> None:
        with patch.dict("sys.modules", {"redis": None, "redis.asyncio": None}):
            import importlib

            import fastapi_keycloak_rbac.cache as cache_mod

            importlib.reload(cache_mod)
            with pytest.raises(ImportError, match="redis"):
                cache_mod.TokenCache(redis_url="redis://localhost")
