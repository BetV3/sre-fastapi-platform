"""Custom exception classes and handlers."""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger

logger = get_logger(__name__)


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str
    message: str
    details: dict[str, Any] | None = None
    request_id: str | None = None


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class NotFoundError(AppException):
    """Resource not found exception."""

    def __init__(self, message: str = "Resource not found", **kwargs: Any) -> None:
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            **kwargs,
        )


class BadRequestError(AppException):
    """Bad request exception."""

    def __init__(self, message: str = "Bad request", **kwargs: Any) -> None:
        super().__init__(
            message=message,
            error_code="BAD_REQUEST",
            status_code=status.HTTP_400_BAD_REQUEST,
            **kwargs,
        )


class UnauthorizedError(AppException):
    """Unauthorized access exception."""

    def __init__(self, message: str = "Unauthorized", **kwargs: Any) -> None:
        super().__init__(
            message=message,
            error_code="UNAUTHORIZED",
            status_code=status.HTTP_401_UNAUTHORIZED,
            **kwargs,
        )


class ForbiddenError(AppException):
    """Forbidden access exception."""

    def __init__(self, message: str = "Forbidden", **kwargs: Any) -> None:
        super().__init__(
            message=message,
            error_code="FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
            **kwargs,
        )


class ConflictError(AppException):
    """Resource conflict exception."""

    def __init__(self, message: str = "Conflict", **kwargs: Any) -> None:
        super().__init__(
            message=message,
            error_code="CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
            **kwargs,
        )


def setup_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers with the FastAPI application."""

    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request, exc: AppException
    ) -> JSONResponse:
        """Handle application exceptions."""
        logger.warning(
            "app_exception",
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=exc.error_code,
                message=exc.message,
                details=exc.details,
                request_id=request.headers.get("X-Request-ID"),
            ).model_dump(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """Handle HTTP exceptions."""
        logger.warning(
            "http_exception",
            status_code=exc.status_code,
            detail=exc.detail,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error="HTTP_ERROR",
                message=str(exc.detail),
                request_id=request.headers.get("X-Request-ID"),
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle request validation errors."""
        errors = []
        for error in exc.errors():
            errors.append(
                {
                    "field": ".".join(str(loc) for loc in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"],
                }
            )
        logger.warning("validation_error", errors=errors)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                error="VALIDATION_ERROR",
                message="Request validation failed",
                details={"errors": errors},
                request_id=request.headers.get("X-Request-ID"),
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle unhandled exceptions."""
        logger.exception("unhandled_exception", error=str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error="INTERNAL_ERROR",
                message="An unexpected error occurred",
                request_id=request.headers.get("X-Request-ID"),
            ).model_dump(),
        )
