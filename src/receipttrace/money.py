"""Explicit numeric conventions; never infer locale from a separator."""

import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

NumberPolicy = Literal["idr-grouped", "decimal-dot", "decimal-comma", "brl-grouped", "usd-grouped"]
POLICIES: tuple[NumberPolicy, ...] = (
    "idr-grouped",
    "decimal-dot",
    "decimal-comma",
    "brl-grouped",
    "usd-grouped",
)


@dataclass(frozen=True)
class Number:
    raw: str | None
    value: Decimal | None
    status: Literal["missing", "invalid", "parsed"]
    reason: str | None = None


def money(raw: str | None, policy: NumberPolicy, *, signed: bool = False) -> Number:
    if policy not in POLICIES:
        raise ValueError(f"Unsupported numeric policy: {policy}")
    if raw is None or not raw.strip():
        return Number(raw, None, "missing")
    if len(raw) > 64:
        return Number(raw, None, "invalid", "text_too_long")
    text = raw.strip()
    if policy == "idr-grouped":
        text = re.sub(r"^Rp\.?\s*", "", text, flags=re.IGNORECASE)
        pattern = r"-?(?:[0-9]{1,18}|[0-9]{1,3}(?:,[0-9]{3}){1,5}|[0-9]{1,3}(?:\.[0-9]{3}){1,5})"
        normalized = text.replace(",", "").replace(".", "")
    elif policy in {"brl-grouped", "usd-grouped"}:
        comma = policy == "brl-grouped"
        text = re.sub(r"^R\$\s*" if comma else r"^\$\s*", "", text)
        group, decimal = (".", ",") if comma else (",", ".")
        pattern = (
            rf"-?(?:[0-9]{{1,18}}|[0-9]{{1,3}}(?:{re.escape(group)}[0-9]{{3}}){{1,5}})"
            rf"(?:{re.escape(decimal)}[0-9]{{1,4}})?"
        )
        normalized = text.replace(group, "").replace(decimal, ".")
    else:
        separator = "." if policy == "decimal-dot" else ","
        pattern = rf"-?[0-9]{{1,18}}(?:{re.escape(separator)}[0-9]{{1,4}})?"
        normalized = text.replace(separator, ".")
    if not re.fullmatch(pattern, text):
        return Number(raw, None, "invalid", "unsupported_numeric_format")
    value = Decimal(normalized)
    if value < 0 and not signed:
        return Number(raw, None, "invalid", "negative_amount")
    return Number(raw, value, "parsed")


def quantity(raw: str | None) -> Number:
    """Quantity uses an explicit decimal dot, with optional leading/trailing x."""
    if raw is None or not raw.strip():
        return Number(raw, None, "missing")
    match = re.fullmatch(r"\s*(?:[xX]\s*)?([0-9]{1,9}(?:\.[0-9]{1,4})?)\s*(?:[xX])?\s*", raw)
    if match is None or len(raw) > 64:
        return Number(raw, None, "invalid", "unsupported_quantity_format")
    value = Decimal(match.group(1))
    if value <= 0:
        return Number(raw, None, "invalid", "nonpositive_quantity")
    return Number(raw, value, "parsed")
