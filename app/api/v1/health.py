"""Health check endpoints."""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.models.common import HealthResponse
from app.services.health import HealthService

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Get detailed health status of the application and its dependencies.",
)
async def health_check() -> HealthResponse:
    """Perform a comprehensive health check."""
    return await HealthService.get_health()


@router.get(
    "/health/live",
    summary="Liveness Probe",
    description="Kubernetes liveness probe endpoint.",
)
async def liveness() -> dict:
    """Check if the service is alive."""
    return await HealthService.get_liveness()


@router.get(
    "/health/ready",
    summary="Readiness Probe",
    description="Kubernetes readiness probe endpoint.",
)
async def readiness() -> JSONResponse:
    """Check if the service is ready to accept traffic."""
    result = await HealthService.get_readiness()
    status_code = status.HTTP_200_OK if result["ready"] else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(content=result, status_code=status_code)
