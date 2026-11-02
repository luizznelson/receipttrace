"""Sum-of-items check for uploaded receipts.

A receipt that lists purchases and prints only a total can still be checked: the printed item
amounts should add up to it. The check is deliberately conservative. It never turns a missing
amount into zero, it stays unavailable when the receipt also prints adjustments it cannot
reconcile, and an exact match does not prove that every item was read.
"""

from collections.abc import Mapping, Sequence
from decimal import Decimal, localcontext
from typing import Any

from receipttrace.money import NumberPolicy, money

MAX_ITEMS = 200


def check_item_sum(
    items: Sequence[Mapping[str, Any]],
    fields: Mapping[str, str | None],
    policy: NumberPolicy,
    *,
    nested: bool = False,
) -> dict[str, Any]:
    """Compare item amounts with the subtotal, or with the total if nothing else is printed."""
    result: dict[str, Any] = {
        "status": "unavailable",
        "reason": None,
        "target": None,
        "items": len(items),
        "sum": None,
        "expected": None,
        "difference": None,
        "unreadable_items": [],
    }
    if not items:
        result["reason"] = "no_items"
        return result
    if nested:
        result["reason"] = "nested_items"
        return result
    if len(items) > MAX_ITEMS:
        result["reason"] = "too_many_items"
        return result
    amounts = [money(item.get("amount"), policy) for item in items]
    unreadable = [index for index, number in enumerate(amounts) if number.value is None]
    if unreadable:
        result["reason"] = "item_amount_unreadable"
        result["unreadable_items"] = unreadable
        return result
    subtotal = money(fields.get("subtotal"), policy)
    adjustments = [
        money(fields.get(name), policy, signed=name == "discount")
        for name in ("discount", "tax", "service")
    ]
    if subtotal.status != "missing":
        target_name, target = "subtotal", subtotal
    elif any(number.status != "missing" for number in adjustments):
        result["reason"] = "adjustments_present"
        return result
    else:
        target_name, target = "total", money(fields.get("total"), policy)
    result["target"] = target_name
    if target.status == "missing":
        result["reason"] = f"{target_name}_missing"
        return result
    if target.value is None:
        result["reason"] = f"{target_name}_invalid"
        return result
    with localcontext() as context:
        # The numeric grammar bounds every operand; this precision avoids context rounding.
        context.prec = 80
        total = sum((number.value for number in amounts if number.value is not None), Decimal(0))
        difference = total - target.value
    result.update(
        status="match" if difference == 0 else "mismatch",
        sum=total,
        expected=target.value,
        difference=difference,
    )
    return result
