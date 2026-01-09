"""Health check service."""

import time
from typing import Any

from app.config import settings
from app.core.logging import get_logger
from app.core.redis import redis_client
from app.models.common import HealthCheck, HealthResponse, StatusEnum

logger = get_logger(__name__)


class HealthService:
    """Service for performing health checks."""

    @staticmethod
    async def check_redis() -> HealthCheck:
        """Check Redis connectivity."""
        start = time.perf_counter()
        try:
            async with redis_client() as client:
                await client.ping()
            latency = (time.perf_counter() - start) * 1000
            return HealthCheck(
                name="redis",
                status=StatusEnum.HEALTHY,
                latency_ms=round(latency, 2),
            )
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            logger.error("redis_health_check_failed", error=str(e))
            return HealthCheck(
                name="redis",
                status=StatusEnum.UNHEALTHY,
                latency_ms=round(latency, 2),
                message=str(e),
            )

    @classmethod
    async def get_health(cls, include_details: bool = True) -> HealthResponse:
        """Get overall health status."""
        checks: list[HealthCheck] = []

        if include_details:
            # Add all health checks
            checks.append(await cls.check_redis())

        # Determine overall status
        if not checks:
            overall_status = StatusEnum.HEALTHY
        elif any(c.status == StatusEnum.UNHEALTHY for c in checks):
            overall_status = StatusEnum.UNHEALTHY
        elif any(c.status == StatusEnum.DEGRADED for c in checks):
            overall_status = StatusEnum.DEGRADED
        else:
            overall_status = StatusEnum.HEALTHY

        return HealthResponse(
            status=overall_status,
            version=settings.app_version,
            checks=checks,
        )

    @classmethod
    async def get_readiness(cls) -> dict[str, Any]:
        """Check if the service is ready to accept traffic."""
        health = await cls.get_health()
        return {
            "ready": health.status != StatusEnum.UNHEALTHY,
            "status": health.status.value,
        }

    @staticmethod
    async def get_liveness() -> dict[str, Any]:
        """Check if the service is alive."""
        return {"alive": True}
