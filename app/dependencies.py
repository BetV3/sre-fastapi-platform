"""FastAPI dependency injection."""

from typing import Annotated, AsyncGenerator

from fastapi import Depends
from redis.asyncio import Redis

from app.config import Settings, get_settings
from app.core.redis import get_redis


# Settings dependency
SettingsDep = Annotated[Settings, Depends(get_settings)]

# Redis dependency
async def get_redis_client() -> AsyncGenerator[Redis, None]:
    """Get Redis client as a dependency."""
    async for client in get_redis():
        yield client


RedisDep = Annotated[Redis, Depends(get_redis_client)]
