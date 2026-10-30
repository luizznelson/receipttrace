"""Receipt input contracts and conservative arithmetic validation."""

from collections import Counter
from dataclasses import asdict, dataclass
from decimal import Decimal, localcontext
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from receipttrace.money import Number, NumberPolicy, money, quantity


class RawItem(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    description: str | None = None
    quantity: str | None = None
    unit_price: str | None = None
    amount: str | None = None
    discount: str | None = None
    children: list[RawItem] = Field(default_factory=list, max_length=100)


class RawReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    document_id: str = Field(min_length=1, max_length=200)
    currency: str | None = None
    items: list[RawItem] = Field(default_factory=list, max_length=1000)
    items_complete: bool = False
    subtotal: str | None = None
    discount: str | None = None
    tax: str | None = None
    service: str | None = None
    total: str | None = None


@dataclass(frozen=True)
class Item:
    description: str | None
    quantity: Number
    unit_price: Number
    amount: Number
    discount: Number
    children: tuple[Item, ...]


@dataclass(frozen=True)
class Receipt:
    document_id: str
    currency: str | None
    items: tuple[Item, ...]
    items_complete: bool
    subtotal: Number
    discount: Number
    tax: Number
    service: Number
    total: Number


@dataclass(frozen=True)
class Check:
    code: str
    path: str
    status: Literal["pass", "mismatch", "skipped", "invalid"]
    reason: str | None = None
    expected: Decimal | None = None
    observed: Decimal | None = None
    difference: Decimal | None = None


def normalize(raw: RawReceipt, policy: NumberPolicy) -> Receipt:
    def item(value: RawItem) -> Item:
        return Item(
            value.description,
            quantity(value.quantity),
            money(value.unit_price, policy),
            money(value.amount, policy),
            money(value.discount, policy, signed=True),
            tuple(item(child) for child in value.children),
        )

    return Receipt(
        raw.document_id,
        raw.currency,
        tuple(item(value) for value in raw.items),
        raw.items_complete,
        money(raw.subtotal, policy),
        money(raw.discount, policy, signed=True),
        money(raw.tax, policy),
        money(raw.service, policy),
        money(raw.total, policy),
    )


def validate(receipt: Receipt, tolerance: Decimal = Decimal("0")) -> tuple[Check, ...]:
    if not isinstance(tolerance, Decimal) or not tolerance.is_finite() or tolerance < 0:
        raise ValueError("Tolerance must be a finite, nonnegative Decimal")
    checks: list[Check] = []

    def compare(code: str, path: str, expected: Decimal, observed: Decimal) -> None:
        difference = observed - expected
        checks.append(
            Check(
                code,
                path,
                "pass" if abs(difference) <= tolerance else "mismatch",
                expected=expected,
                observed=observed,
                difference=difference,
            )
        )

    def invalid_fields(fields: dict[str, Number], path: str) -> None:
        for name, field in fields.items():
            if field.status == "invalid":
                checks.append(Check("numeric_field", f"{path}{name}", "invalid", field.reason))

    def inspect_item(value: Item, path: str) -> None:
        invalid_fields(
            {
                "quantity": value.quantity,
                "unit_price": value.unit_price,
                "amount": value.amount,
                "discount": value.discount,
            },
            path + ".",
        )
        q, unit, amount, discount = (
            value.quantity.value,
            value.unit_price.value,
            value.amount.value,
            value.discount.value,
        )
        if value.children:
            checks.append(Check("item_total", path, "skipped", "nested_item_semantics_unknown"))
        elif q is None or unit is None or amount is None or discount is None:
            checks.append(Check("item_total", path, "skipped", "missing_or_invalid_component"))
        else:
            compare("item_total", path, q * unit - abs(discount), amount)
        for index, child in enumerate(value.children):
            inspect_item(child, f"{path}.children[{index}]")

    # The accepted numeric grammar bounds operands; this precision avoids context rounding.
    with localcontext() as context:
        context.prec = 80
        invalid_fields(
            {
                "subtotal": receipt.subtotal,
                "discount": receipt.discount,
                "tax": receipt.tax,
                "service": receipt.service,
                "total": receipt.total,
            },
            "",
        )
        for index, value in enumerate(receipt.items):
            inspect_item(value, f"items[{index}]")
        amounts = [value.amount.value for value in receipt.items]
        if (
            not receipt.items_complete
            or not amounts
            or any(x is None for x in amounts)
            or any(value.children for value in receipt.items)
            or receipt.subtotal.value is None
        ):
            checks.append(Check("subtotal", "subtotal", "skipped", "incomplete_or_nested_items"))
        else:
            compare(
                "subtotal",
                "subtotal",
                sum((x for x in amounts if x is not None), Decimal(0)),
                receipt.subtotal.value,
            )
        subtotal, discount, tax, service, total = (
            receipt.subtotal.value,
            receipt.discount.value,
            receipt.tax.value,
            receipt.service.value,
            receipt.total.value,
        )
        if subtotal is None or discount is None or tax is None or service is None or total is None:
            checks.append(
                Check("receipt_total", "total", "skipped", "missing_or_invalid_component")
            )
        else:
            compare("receipt_total", "total", subtotal - abs(discount) + tax + service, total)
    return tuple(checks)


def report(raw: RawReceipt, policy: NumberPolicy, tolerance: Decimal) -> dict[str, object]:
    receipt = normalize(raw, policy)
    checks = validate(receipt, tolerance)
    return {
        "schema_version": "1",
        "rules_version": "1",
        "numeric_policy": policy,
        "quantity_policy": "decimal-dot-optional-x",
        "tolerance": tolerance,
        "raw": raw.model_dump(),
        "normalized": asdict(receipt),
        "checks": [asdict(check) for check in checks],
        "has_findings": any(check.status in ("invalid", "mismatch") for check in checks),
        "has_skipped_checks": any(check.status == "skipped" for check in checks),
    }


def summarize_validation(validation: dict[str, Any] | None) -> dict[str, Any]:
    counts = Counter(check["status"] for check in validation["checks"]) if validation else Counter()
    if validation is None:
        state = "unavailable"
    elif counts["invalid"] or counts["mismatch"]:
        state = "findings"
    elif not counts["pass"]:
        state = "not_checked"
    elif counts["skipped"]:
        state = "partial"
    else:
        state = "passed"
    return {
        "status": state,
        "passed": counts["pass"],
        "mismatched": counts["mismatch"],
        "invalid": counts["invalid"],
        "skipped": counts["skipped"],
    }
