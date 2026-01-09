"""Application configuration management."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="FastAPI Platform", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    environment: Literal["development", "staging", "production"] = Field(
        default="development", description="Deployment environment"
    )
    debug: bool = Field(default=False, description="Debug mode")

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=1, description="Number of workers")
    reload: bool = Field(default=False, description="Auto-reload on code changes")

    # API
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 prefix")

    # Redis
    redis_url: RedisDsn = Field(
        default="redis://redis:6379/0", description="Redis connection URL"
    )
    redis_pool_size: int = Field(default=10, description="Redis connection pool size")

    # CORS
    cors_origins: list[str] = Field(
        default=["*"], description="Allowed CORS origins"
    )
    cors_allow_credentials: bool = Field(default=True, description="Allow credentials")
    cors_allow_methods: list[str] = Field(default=["*"], description="Allowed methods")
    cors_allow_headers: list[str] = Field(default=["*"], description="Allowed headers")

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )
    log_format: Literal["json", "text"] = Field(
        default="json", description="Log output format"
    )

    # Metrics
    metrics_enabled: bool = Field(default=True, description="Enable Prometheus metrics")

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
