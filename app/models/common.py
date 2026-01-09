"""Common models shared across the application."""

from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class StatusEnum(str, Enum):
    """Status enumeration."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class HealthCheck(BaseModel):
    """Individual health check result."""

    name: str
    status: StatusEnum
    latency_ms: float | None = None
    message: str | None = None


class HealthResponse(BaseModel):
    """Health check response model."""

    status: StatusEnum
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str
    checks: list[HealthCheck] = Field(default_factory=list)


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""

    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        """Create a paginated response."""
        pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str
    data: dict[str, Any] | None = None
