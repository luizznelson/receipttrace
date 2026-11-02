"""Sum-of-items check: conservative states, no invented zeros, bounded API input."""

from decimal import Decimal
from typing import Any

import pytest

from receipttrace.item_sum import MAX_ITEMS, check_item_sum

# The 23 printed lines of a real Brazilian NFC-e (supermarket); the printed total is 291,54.
NFCE_AMOUNTS = [
    "10,95", "9,88", "6,75", "6,75", "26,75", "26,75", "12,85", "25,82",
    "8,25", "8,25", "8,20", "3,61", "1,32", "12,85", "12,85", "12,45",
    "12,45", "4,55", "4,55", "12,45", "3,98", "3,98", "55,30",
]  # fmt: skip


def lines(amounts: list[str | None]) -> list[dict[str, Any]]:
    return [{"description": f"item {i}", "amount": amount} for i, amount in enumerate(amounts)]


def test_printed_items_that_add_up_to_the_only_printed_total_match() -> None:
    result = check_item_sum(lines(NFCE_AMOUNTS), {"total": "291,54"}, "brl-grouped")
    assert result["status"] == "match" and result["target"] == "total"
    assert result["items"] == 23
    assert result["sum"] == result["expected"] == Decimal("291.54")
    assert result["difference"] == 0


def test_one_misread_item_is_reported_with_the_exact_difference() -> None:
    amounts: list[str | None] = [*NFCE_AMOUNTS]
    amounts[7] = "25,92"
    result = check_item_sum(lines(amounts), {"total": "291,54"}, "brl-grouped")
    assert result["status"] == "mismatch"
    assert result["difference"] == Decimal("0.10")


def test_a_missing_item_amount_is_never_treated_as_zero() -> None:
    amounts: list[str | None] = [*NFCE_AMOUNTS]
    amounts[3] = None
    amounts[9] = "not a number"
    result = check_item_sum(lines(amounts), {"total": "291,54"}, "brl-grouped")
    assert result["status"] == "unavailable" and result["reason"] == "item_amount_unreadable"
    assert result["unreadable_items"] == [3, 9] and result["sum"] is None


def test_negative_lines_are_unreadable_not_netted_silently() -> None:
    result = check_item_sum(lines(["10,00", "-2,00"]), {"total": "8,00"}, "brl-grouped")
    assert result["status"] == "unavailable" and result["unreadable_items"] == [1]


def test_subtotal_is_the_target_when_printed() -> None:
    fields = {"subtotal": "10,00", "service": "1,00", "total": "11,00"}
    result = check_item_sum(lines(["4,00", "6,00"]), fields, "brl-grouped")
    assert result["status"] == "match" and result["target"] == "subtotal"


@pytest.mark.parametrize("name", ["tax", "service", "discount"])
def test_adjustments_without_a_subtotal_make_the_check_unavailable(name: str) -> None:
    result = check_item_sum(
        lines(["4,00", "6,00"]), {name: "1,00", "total": "11,00"}, "brl-grouped"
    )
    assert result["status"] == "unavailable" and result["reason"] == "adjustments_present"


@pytest.mark.parametrize(
    ("items", "fields", "reason", "kwargs"),
    [
        ([], {"total": "1,00"}, "no_items", {}),
        (lines(["1,00"]), {}, "total_missing", {}),
        (lines(["1,00"]), {"total": "abc"}, "total_invalid", {}),
        (lines(["1,00"]), {"subtotal": "abc", "total": "1,00"}, "subtotal_invalid", {}),
        (lines(["1,00"]), {"total": "1,00"}, "nested_items", {"nested": True}),
        (lines(["0,01"] * (MAX_ITEMS + 1)), {"total": "2,01"}, "too_many_items", {}),
    ],
)
def test_unavailable_states_name_their_reason(
    items: list[dict[str, Any]], fields: dict[str, str], reason: str, kwargs: dict[str, Any]
) -> None:
    result = check_item_sum(items, fields, "brl-grouped", **kwargs)
    assert result["status"] == "unavailable" and result["reason"] == reason


def test_numeric_policy_decides_separators() -> None:
    comma = check_item_sum(lines(["1.234,50", "0,50"]), {"total": "1.235,00"}, "brl-grouped")
    dot = check_item_sum(lines(["1,234.50", "0.50"]), {"total": "1,235.00"}, "usd-grouped")
    wrong = check_item_sum(lines(["1.234,50"]), {"total": "1.234,50"}, "usd-grouped")
    assert comma["status"] == dot["status"] == "match"
    assert wrong["status"] == "unavailable"


def test_validation_endpoint_checks_edited_items_and_bounds_input() -> None:
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx2")
    from fastapi.testclient import TestClient

    from receipttrace.web import create_app

    client = TestClient(create_app(allow_uploads=True))
    raw = {"document_id": "synthetic", "total": "291,54"}
    body: dict[str, Any] = {
        "raw": raw,
        "items": lines(NFCE_AMOUNTS),
        "policy": "brl-grouped",
    }
    response = client.post("/api/uploads/validate", json=body)
    assert response.status_code == 200
    assert response.json()["items_check"]["status"] == "match"
    body["items"][0]["amount"] = "10,00"
    assert client.post("/api/uploads/validate", json=body).json()["items_check"]["status"] == (
        "mismatch"
    )
    body["items"] = []
    assert client.post("/api/uploads/validate", json=body).json()["items_check"]["reason"] == (
        "no_items"
    )
    body["items"] = lines(["1,00"] * (MAX_ITEMS + 1))
    assert client.post("/api/uploads/validate", json=body).status_code == 422
    body["items"] = [{"description": "x" * 201, "amount": "1,00"}]
    assert client.post("/api/uploads/validate", json=body).status_code == 422
    body["items"] = [{"amount": "1,00", "unexpected": "field"}]
    assert client.post("/api/uploads/validate", json=body).status_code == 422
