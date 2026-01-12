"""Settings dataclasses for BerAPI configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


def _parse_optional_float(value: str | None) -> float | None:
    """Parse optional float from string."""
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _parse_bool(value: str | None, default: bool = True) -> bool:
    """Parse boolean from string."""
    if value is None:
        return default
    return value.lower() in ("true", "1", "yes", "on")


@dataclass
class LoggingSettings:
    """Logging configuration."""

    level: str = "INFO"
    format: str = "json"  # "json" or "console"
    log_request_body: bool = True
    log_response_body: bool = True
    log_headers: bool = True
    log_curl: bool = True
    redact_headers: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {"authorization", "x-api-key", "cookie", "x-auth-token"}
        )
    )


@dataclass
class RetrySettings:
    """Retry configuration."""

    enabled: bool = True
    max_retries: int = 3
    backoff_factor: float = 0.5
    backoff_max: float = 60.0
    retry_statuses: frozenset[int] = field(
        default_factory=lambda: frozenset({429, 500, 502, 503, 504})
    )
    jitter: bool = True


@dataclass
class Settings:
    """Main configuration for BerAPI client."""

    base_url: str | None = None
    timeout: float = 30.0
    max_response_time: float | None = None  # None = no limit
    verify_ssl: bool = True

    headers: dict[str, str] = field(default_factory=dict)

    logging: LoggingSettings = field(default_factory=LoggingSettings)
    retry: RetrySettings = field(default_factory=RetrySettings)

    # OpenAPI validation
    openapi_spec_path: str | None = None
    openapi_validate_requests: bool = False
    openapi_validate_responses: bool = False

    @classmethod
    def from_env(cls) -> Settings:
        """Create settings from environment variables."""
        return cls(
            base_url=os.getenv("BERAPI_BASE_URL"),
            timeout=float(os.getenv("BERAPI_TIMEOUT", "30.0")),
            max_response_time=_parse_optional_float(
                os.getenv("BERAPI_MAX_RESPONSE_TIME")
            ),
            verify_ssl=_parse_bool(os.getenv("BERAPI_VERIFY_SSL"), default=True),
            logging=LoggingSettings(
                level=os.getenv("BERAPI_LOG_LEVEL", "INFO"),
                format=os.getenv("BERAPI_LOG_FORMAT", "json"),
                log_request_body=_parse_bool(
                    os.getenv("BERAPI_LOG_REQUEST_BODY"), default=True
                ),
                log_response_body=_parse_bool(
                    os.getenv("BERAPI_LOG_RESPONSE_BODY"), default=True
                ),
                log_headers=_parse_bool(os.getenv("BERAPI_LOG_HEADERS"), default=True),
                log_curl=_parse_bool(os.getenv("BERAPI_LOG_CURL"), default=True),
            ),
            retry=RetrySettings(
                enabled=_parse_bool(os.getenv("BERAPI_RETRY_ENABLED"), default=True),
                max_retries=int(os.getenv("BERAPI_MAX_RETRIES", "3")),
                backoff_factor=float(os.getenv("BERAPI_BACKOFF_FACTOR", "0.5")),
                backoff_max=float(os.getenv("BERAPI_BACKOFF_MAX", "60.0")),
                jitter=_parse_bool(os.getenv("BERAPI_RETRY_JITTER"), default=True),
            ),
            openapi_spec_path=os.getenv("BERAPI_OPENAPI_SPEC"),
        )

    def merge(self, overrides: dict[str, Any]) -> Settings:
        """Create new settings with overrides applied."""
        import copy

        new_settings = copy.deepcopy(self)

        for key, value in overrides.items():
            if hasattr(new_settings, key):
                if key == "logging" and isinstance(value, dict):
                    for log_key, log_value in value.items():
                        if hasattr(new_settings.logging, log_key):
                            setattr(new_settings.logging, log_key, log_value)
                elif key == "retry" and isinstance(value, dict):
                    for retry_key, retry_value in value.items():
                        if hasattr(new_settings.retry, retry_key):
                            setattr(new_settings.retry, retry_key, retry_value)
                else:
                    setattr(new_settings, key, value)

        return new_settings
