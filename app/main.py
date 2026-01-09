"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1 import router as api_v1_router
from app.config import settings
from app.core.exceptions import setup_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.core.middleware import RequestContextMiddleware
from app.core.redis import close_redis_pool, init_redis_pool

# Initialize logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    logger.info(
        "application_startup",
        app_name=settings.app_name,
        environment=settings.environment,
        version=settings.app_version,
    )

    # Initialize Redis pool
    await init_redis_pool()

    yield

    # Shutdown
    logger.info("application_shutdown")
    await close_redis_pool()


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Production-ready FastAPI boilerplate with observability",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    # Add request context middleware
    app.add_middleware(RequestContextMiddleware)

    # Setup exception handlers
    setup_exception_handlers(app)

    # Mount Prometheus metrics endpoint
    if settings.metrics_enabled:
        metrics_app = make_asgi_app()
        app.mount("/metrics", metrics_app)

    # Include API routers
    app.include_router(api_v1_router, prefix=settings.api_v1_prefix)

    # Root endpoint
    @app.get("/", include_in_schema=False)
    async def root() -> dict:
        return {
            "app": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs" if not settings.is_production else None,
        }

    return app


app = create_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        workers=settings.workers,
        log_level=settings.log_level.lower(),
    )
