"""Curl command generation utilities."""

from __future__ import annotations

import json
import shlex
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from berapi.middleware.base import RequestContext


def generate_curl(context: RequestContext) -> str:
    """Generate a curl command from a request context.

    Args:
        context: Request context to generate curl from.

    Returns:
        Curl command string.
    """
    parts = ["curl", "-X", context.method]

    # Add URL
    url = context.url
    if context.params:
        param_str = "&".join(f"{k}={v}" for k, v in context.params.items())
        url = f"{url}?{param_str}"
    parts.append(shlex.quote(url))

    # Add headers
    for key, value in context.headers.items():
        # Skip internal headers
        if key.lower() in ("content-length", "host"):
            continue
        parts.extend(["-H", shlex.quote(f"{key}: {value}")])

    # Add body
    if context.json_body is not None:
        body_str = json.dumps(context.json_body)
        parts.extend(["-d", shlex.quote(body_str)])
    elif context.data is not None:
        parts.extend(["-d", shlex.quote(str(context.data))])

    return " ".join(parts)


def generate_curl_from_response(response: "RequestContext") -> str:
    """Generate curl from a requests Response object.

    This is a compatibility wrapper for the old API.

    Args:
        response: Response object with request attribute.

    Returns:
        Curl command string.
    """
    return generate_curl(response)
