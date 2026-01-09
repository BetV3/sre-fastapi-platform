"""Prometheus metrics configuration."""

from prometheus_client import Counter, Gauge, Histogram, Info

from app.config import settings

# Application info
APP_INFO = Info("app_info", "Application information")
APP_INFO.info(
    {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }
)

# Request metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

REQUEST_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently in progress",
    ["method", "endpoint"],
)

# Redis metrics
REDIS_OPERATIONS = Counter(
    "redis_operations_total",
    "Total Redis operations",
    ["operation", "status"],
)

REDIS_LATENCY = Histogram(
    "redis_operation_duration_seconds",
    "Redis operation latency in seconds",
    ["operation"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)

# Business metrics (customize as needed)
ACTIVE_USERS = Gauge(
    "active_users_total",
    "Number of active users",
)

EVENTS_PROCESSED = Counter(
    "events_processed_total",
    "Total events processed",
    ["event_type", "status"],
)
