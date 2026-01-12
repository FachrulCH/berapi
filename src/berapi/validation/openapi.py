"""OpenAPI validation utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import requests


# Cache for loaded specs
_spec_cache: dict[str, Any] = {}


def load_openapi_spec(spec_path: str) -> Any:
    """Load OpenAPI specification from file.

    Args:
        spec_path: Path to OpenAPI spec (YAML or JSON).

    Returns:
        Loaded OpenAPI spec.
    """
    if spec_path in _spec_cache:
        return _spec_cache[spec_path]

    import yaml

    with open(spec_path) as f:
        if spec_path.endswith((".yaml", ".yml")):
            spec = yaml.safe_load(f)
        else:
            import json

            spec = json.load(f)

    _spec_cache[spec_path] = spec
    return spec


def validate_openapi_response(
    response: "requests.Response",
    operation_id: str,
    spec_path: str | None = None,
) -> list[str]:
    """Validate response against OpenAPI specification.

    Args:
        response: Response to validate.
        operation_id: Operation ID in the spec.
        spec_path: Path to OpenAPI spec file.

    Returns:
        List of validation error messages. Empty if valid.
    """
    errors: list[str] = []

    if spec_path is None:
        errors.append("OpenAPI spec path not provided")
        return errors

    try:
        from openapi_core import OpenAPI

        spec = load_openapi_spec(spec_path)
        openapi = OpenAPI.from_dict(spec)

        # Find the operation
        operation = None
        path_pattern = None
        method = response.request.method.lower() if response.request.method else "get"

        for path, path_item in spec.get("paths", {}).items():
            if method in path_item:
                op = path_item[method]
                if op.get("operationId") == operation_id:
                    operation = op
                    path_pattern = path
                    break

        if operation is None:
            errors.append(f"Operation '{operation_id}' not found in spec")
            return errors

        # Validate response
        status_code = str(response.status_code)
        responses = operation.get("responses", {})

        if status_code not in responses and "default" not in responses:
            errors.append(
                f"Status code {status_code} not defined for operation '{operation_id}'"
            )
            return errors

        response_spec = responses.get(status_code, responses.get("default", {}))

        # Validate content type
        content_type = response.headers.get("Content-Type", "")
        if "content" in response_spec:
            valid_types = list(response_spec["content"].keys())
            if not any(ct in content_type for ct in valid_types):
                errors.append(
                    f"Content-Type '{content_type}' not in allowed types {valid_types}"
                )

        # Validate response body against schema
        if "content" in response_spec and "application/json" in response_spec["content"]:
            schema = response_spec["content"]["application/json"].get("schema")
            if schema:
                try:
                    import jsonschema

                    # Resolve $ref if present
                    schema = _resolve_refs(schema, spec)
                    jsonschema.validate(response.json(), schema)
                except jsonschema.ValidationError as e:
                    errors.append(f"Response body validation failed: {e.message}")
                except Exception as e:
                    errors.append(f"Response body validation error: {str(e)}")

    except ImportError:
        errors.append("openapi-core package not installed")
    except Exception as e:
        errors.append(f"OpenAPI validation error: {str(e)}")

    return errors


def _resolve_refs(schema: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    """Resolve $ref references in schema.

    Args:
        schema: Schema that may contain $ref.
        spec: Full OpenAPI spec for resolving refs.

    Returns:
        Schema with refs resolved.
    """
    if "$ref" in schema:
        ref_path = schema["$ref"]
        if ref_path.startswith("#/"):
            parts = ref_path[2:].split("/")
            resolved = spec
            for part in parts:
                resolved = resolved.get(part, {})
            return _resolve_refs(resolved, spec)
    return schema
