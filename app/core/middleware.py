"""Custom middleware for the application."""

import time
import uuid
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger, request_id_ctx
from app.core.metrics import REQUEST_COUNT, REQUEST_IN_PROGRESS, REQUEST_LATENCY

logger = get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to add request context (ID, timing, logging)."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        """Process the request and add context."""
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_ctx.set(request_id)

        # Get endpoint for metrics (normalize path)
        endpoint = request.url.path

        # Track request timing
        start_time = time.perf_counter()

        # Track in-progress requests
        REQUEST_IN_PROGRESS.labels(method=request.method, endpoint=endpoint).inc()

        # Log request start
        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            query=str(request.query_params) if request.query_params else None,
            client_ip=request.client.host if request.client else None,
        )

        try:
            response = await call_next(request)
        except Exception as e:
            # Record failed request metrics
            REQUEST_COUNT.labels(
                method=request.method, endpoint=endpoint, status_code=500
            ).inc()
            REQUEST_IN_PROGRESS.labels(method=request.method, endpoint=endpoint).dec()
            logger.exception(
                "request_failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
            )
            raise

        # Calculate duration
        duration_seconds = time.perf_counter() - start_time
        duration_ms = duration_seconds * 1000

        # Record metrics
        REQUEST_COUNT.labels(
            method=request.method, endpoint=endpoint, status_code=response.status_code
        ).inc()
        REQUEST_LATENCY.labels(method=request.method, endpoint=endpoint).observe(
            duration_seconds
        )
        REQUEST_IN_PROGRESS.labels(method=request.method, endpoint=endpoint).dec()

        # Add headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        # Log request completion
        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )

        return response
