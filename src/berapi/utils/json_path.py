"""JSON path utilities for dot notation access."""

from __future__ import annotations

from typing import Any


def get_by_path(data: dict[str, Any] | list[Any], path: str, default: Any = None) -> Any:
    """Get a value from nested data using dot notation.

    Supports both dict and list access:
    - "user.name" -> data["user"]["name"]
    - "users.0.name" -> data["users"][0]["name"]
    - "items.0" -> data["items"][0]

    Args:
        data: The data to traverse.
        path: Dot-separated path to the value.
        default: Default value if path not found.

    Returns:
        The value at the path, or default if not found.

    Examples:
        >>> data = {"user": {"name": "John", "addresses": [{"city": "NYC"}]}}
        >>> get_by_path(data, "user.name")
        'John'
        >>> get_by_path(data, "user.addresses.0.city")
        'NYC'
        >>> get_by_path(data, "user.missing", "default")
        'default'
    """
    if not path:
        return data

    current: Any = data
    parts = path.split(".")

    for part in parts:
        if current is None:
            return default

        # Try list index access
        if isinstance(current, list):
            try:
                index = int(part)
                if 0 <= index < len(current):
                    current = current[index]
                else:
                    return default
            except ValueError:
                return default
        # Dict access
        elif isinstance(current, dict):
            if part in current:
                current = current[part]
            else:
                return default
        else:
            return default

    return current


def has_path(data: dict[str, Any] | list[Any], path: str) -> bool:
    """Check if a path exists in nested data.

    Args:
        data: The data to check.
        path: Dot-separated path to check.

    Returns:
        True if the path exists, False otherwise.

    Examples:
        >>> data = {"user": {"name": "John"}}
        >>> has_path(data, "user.name")
        True
        >>> has_path(data, "user.email")
        False
    """
    sentinel = object()
    return get_by_path(data, path, sentinel) is not sentinel


def set_by_path(data: dict[str, Any], path: str, value: Any) -> None:
    """Set a value in nested data using dot notation.

    Creates intermediate dicts as needed.

    Args:
        data: The data to modify.
        path: Dot-separated path to set.
        value: Value to set.

    Examples:
        >>> data = {}
        >>> set_by_path(data, "user.name", "John")
        >>> data
        {'user': {'name': 'John'}}
    """
    if not path:
        return

    parts = path.split(".")
    current = data

    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]

    current[parts[-1]] = value
