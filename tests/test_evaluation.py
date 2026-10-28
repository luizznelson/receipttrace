"""Evaluation includes abstentions and distinguishes unannotated fields."""

import pytest

from receipttrace.evaluation import field_result


@pytest.mark.parametrize(
    "expected,predicted,outcome",
    [
        ("1,000", "1.000", "correct"),
        ("1,000", "2,000", "wrong_value"),
        ("1,000", None, "missed"),
        ("1,000", "unknown", "missed"),
        (None, "1,000", "unannotated_prediction"),
        (None, None, "unannotated_abstention"),
        ("NaN", "1,000", "invalid_reference"),
    ],
)
def test_field_outcomes(expected: str | None, predicted: str | None, outcome: str) -> None:
    assert field_result(expected, predicted) == outcome


def test_signed_discounts_compare_magnitudes() -> None:
    assert field_result("-1,000", "1,000", signed=True) == "correct"
