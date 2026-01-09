"""Redis client and utilities."""

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

import redis.asyncio as redis
from redis.asyncio import ConnectionPool, Redis

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Global connection pool
_pool: ConnectionPool | None = None


async def init_redis_pool() -> ConnectionPool:
    """Initialize the Redis connection pool."""
    global _pool
    if _pool is None:
        logger.info("redis_pool_init", url=str(settings.redis_url))
        _pool = ConnectionPool.from_url(
            str(settings.redis_url),
            max_connections=settings.redis_pool_size,
            decode_responses=True,
        )
    return _pool


async def close_redis_pool() -> None:
    """Close the Redis connection pool."""
    global _pool
    if _pool is not None:
        logger.info("redis_pool_close")
        await _pool.disconnect()
        _pool = None


async def get_redis() -> AsyncGenerator[Redis, None]:
    """Get a Redis client from the connection pool."""
    pool = await init_redis_pool()
    client = Redis(connection_pool=pool)
    try:
        yield client
    finally:
        await client.aclose()


@asynccontextmanager
async def redis_client() -> AsyncGenerator[Redis, None]:
    """Context manager for Redis client."""
    async for client in get_redis():
        yield client
        break


class RedisCache:
    """Redis-based caching utility."""

    def __init__(self, prefix: str = "cache", default_ttl: int = 3600) -> None:
        """Initialize the cache with a key prefix and default TTL."""
        self.prefix = prefix
        self.default_ttl = default_ttl

    def _make_key(self, key: str) -> str:
        """Create a prefixed cache key."""
        return f"{self.prefix}:{key}"

    async def get(self, key: str) -> str | None:
        """Get a value from the cache."""
        async with redis_client() as client:
            return await client.get(self._make_key(key))

    async def set(
        self, key: str, value: str, ttl: int | None = None
    ) -> bool:
        """Set a value in the cache."""
        async with redis_client() as client:
            return await client.set(
                self._make_key(key),
                value,
                ex=ttl or self.default_ttl,
            )

    async def delete(self, key: str) -> int:
        """Delete a value from the cache."""
        async with redis_client() as client:
            return await client.delete(self._make_key(key))

    async def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        async with redis_client() as client:
            return bool(await client.exists(self._make_key(key)))

    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment a counter in the cache."""
        async with redis_client() as client:
            return await client.incrby(self._make_key(key), amount)

    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration on a key."""
        async with redis_client() as client:
            return await client.expire(self._make_key(key), ttl)

    async def get_json(self, key: str) -> dict[str, Any] | list | None:
        """Get a JSON value from the cache."""
        import json

        value = await self.get(key)
        if value:
            return json.loads(value)
        return None

    async def set_json(
        self, key: str, value: dict[str, Any] | list, ttl: int | None = None
    ) -> bool:
        """Set a JSON value in the cache."""
        import json

        return await self.set(key, json.dumps(value), ttl)


# Default cache instance
cache = RedisCache()
