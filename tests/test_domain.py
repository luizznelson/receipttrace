"""Business rules use explicit synthetic cases, not CORD expected answers."""

from decimal import Decimal, localcontext

import pytest
from pydantic import ValidationError

from receipttrace.domain import RawItem, RawReceipt, normalize, report, validate
from receipttrace.money import money, quantity


@pytest.mark.parametrize(
    "text,expected",
    [
        ("43,181", "43181"),
        ("43.181", "43181"),
        ("Rp 13.000", "13000"),
        ("0", "0"),
        ("1,234,567", "1234567"),
    ],
)
def test_idr_grouping(text: str, expected: str) -> None:
    result = money(text, "idr-grouped")
    assert result.value == Decimal(expected)
    assert result.raw == text


@pytest.mark.parametrize("text", ["1,23", "1.234,567", "NaN", "Infinity", "1e3", "@20.000"])
def test_unsupported_format_is_not_guessed(text: str) -> None:
    assert money(text, "idr-grouped").status == "invalid"


def test_policy_changes_interpretation_explicitly() -> None:
    assert money("1.234", "decimal-dot").value == Decimal("1.234")
    assert money("1.234", "idr-grouped").value == Decimal("1234")
    assert money("10,25", "decimal-comma").value == Decimal("10.25")


@pytest.mark.parametrize("raw", [None, "", "  "])
def test_missing_is_not_zero(raw: str | None) -> None:
    assert money(raw, "idr-grouped").value is None
    assert money(raw, "idr-grouped").status == "missing"


@pytest.mark.parametrize("raw", ["1 x", "x1", "1.00", " 1 "])
def test_quantity_markers(raw: str) -> None:
    assert quantity(raw).value == Decimal(1)


@pytest.mark.parametrize("raw", ["0", "-1", "1,5", "1.00xITEMS", "two", "NaN"])
def test_quantity_rejects_ambiguous_or_nonpositive_values(raw: str) -> None:
    assert quantity(raw).status == "invalid"


def test_strict_contract_rejects_numbers_and_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        RawReceipt.model_validate({"document_id": "fixture", "total": 0.1})
    with pytest.raises(ValidationError):
        RawReceipt.model_validate({"document_id": "fixture", "invented": "value"})


def receipt() -> RawReceipt:
    return RawReceipt(
        document_id="synthetic",
        items_complete=True,
        items=[
            RawItem(
                description="fixture", quantity="3", unit_price="0.10", amount="0.30", discount="0"
            )
        ],
        subtotal="0.30",
        discount="0",
        tax="0",
        service="0",
        total="0.30",
    )


def test_exact_arithmetic_and_raw_preservation() -> None:
    raw = receipt()
    result = report(raw, "decimal-dot", Decimal(0))
    assert not result["has_findings"]
    assert not result["has_skipped_checks"]
    assert {check.status for check in validate(normalize(raw, "decimal-dot"))} == {"pass"}
    assert raw.items[0].unit_price == "0.10"


def test_missing_adjustments_skip_total_instead_of_assuming_zero() -> None:
    raw = RawReceipt(document_id="fixture", subtotal="100", total="100")
    checks = validate(normalize(raw, "idr-grouped"))
    assert next(check for check in checks if check.code == "receipt_total").status == "skipped"


def test_discounts_are_deductions_with_either_sign() -> None:
    for discount in ["10", "-10"]:
        raw = RawReceipt(
            document_id="fixture",
            subtotal="100",
            discount=discount,
            tax="5",
            service="0",
            total="95",
        )
        check = validate(normalize(raw, "idr-grouped"))[-1]
        assert check.status == "pass"


def test_tolerance_and_difference_are_explicit() -> None:
    raw = receipt().model_copy(update={"total": "0.31"})
    normalized = normalize(raw, "decimal-dot")
    assert validate(normalized)[-1].status == "mismatch"
    assert validate(normalized)[-1].difference == Decimal("0.01")
    assert validate(normalized, Decimal("0.01"))[-1].status == "pass"


@pytest.mark.parametrize("value", [Decimal("-1"), Decimal("NaN"), Decimal("Infinity")])
def test_invalid_tolerance(value: Decimal) -> None:
    with pytest.raises(ValueError):
        validate(normalize(receipt(), "decimal-dot"), value)


def test_nested_items_preserved_without_double_counting() -> None:
    raw = RawReceipt(
        document_id="fixture",
        items_complete=True,
        subtotal="100",
        items=[RawItem(amount="100", children=[RawItem(amount="20")])],
    )
    parsed = normalize(raw, "idr-grouped")
    assert parsed.items[0].children[0].amount.value == Decimal(20)
    checks = validate(parsed)
    assert all(check.status == "skipped" for check in checks)


def test_negative_amount_is_invalid_but_negative_discount_is_valid() -> None:
    assert money("-1", "idr-grouped").status == "invalid"
    assert money("-1", "idr-grouped", signed=True).value == Decimal(-1)
    raw = RawReceipt(document_id="fixture", total="-1")
    assert any(check.status == "invalid" for check in validate(normalize(raw, "idr-grouped")))


def test_arithmetic_does_not_depend_on_callers_decimal_context() -> None:
    raw = receipt()
    with localcontext() as context:
        context.prec = 1
        assert all(check.status == "pass" for check in validate(normalize(raw, "decimal-dot")))
