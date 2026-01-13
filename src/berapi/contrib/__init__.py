"""Contrib modules for berapi integrations.

This package contains optional integrations with external tools:
- pytest_plugin: pytest-html report integration
"""

from berapi.contrib.pytest_plugin import (
    create_tracking_client,
    get_tracker,
    pytest_configure,
)

__all__ = [
    "create_tracking_client",
    "get_tracker",
    "pytest_configure",
]
