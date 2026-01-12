"""JSON Schema validation utilities."""

from __future__ import annotations

import json
from typing import Any

import jsonschema
from genson import SchemaBuilder


def validate_json_schema(
    data: dict[str, Any] | list[Any],
    schema: dict[str, Any],
) -> list[str]:
    """Validate data against JSON Schema.

    Args:
        data: Data to validate.
        schema: JSON Schema to validate against.

    Returns:
        List of validation error messages. Empty if valid.
    """
    errors: list[str] = []

    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        errors.append(str(e.message))
        # Collect all errors using a validator
        validator = jsonschema.Draft7Validator(schema)
        for error in validator.iter_errors(data):
            if error.message not in errors:
                path = ".".join(str(p) for p in error.absolute_path)
                if path:
                    errors.append(f"{path}: {error.message}")
                else:
                    errors.append(error.message)

    return errors


def generate_schema_from_sample(sample: dict[str, Any] | list[Any]) -> dict[str, Any]:
    """Generate JSON Schema from a sample.

    Args:
        sample: Sample data to generate schema from.

    Returns:
        Generated JSON Schema.
    """
    builder = SchemaBuilder()
    builder.add_object(sample)
    return builder.to_schema()


def validate_against_sample(
    data: dict[str, Any] | list[Any],
    sample_path: str,
) -> list[str]:
    """Validate data against schema generated from sample.

    Args:
        data: Data to validate.
        sample_path: Path to sample JSON file.

    Returns:
        List of validation error messages. Empty if valid.
    """
    with open(sample_path) as f:
        sample = json.load(f)

    schema = generate_schema_from_sample(sample)
    return validate_json_schema(data, schema)


def load_schema(schema_path: str) -> dict[str, Any]:
    """Load JSON Schema from file.

    Args:
        schema_path: Path to schema file.

    Returns:
        Loaded JSON Schema.
    """
    with open(schema_path) as f:
        return json.load(f)
