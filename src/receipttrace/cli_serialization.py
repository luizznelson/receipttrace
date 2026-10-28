"""JSON output preserves Decimal precision by encoding decimal values as strings."""

from decimal import Decimal


def decimal_json(value: object) -> str:
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"Unsupported JSON type: {type(value).__name__}")
