"""Synthetic layout cases for conservative OCR parsing; no OCR model required."""

from receipttrace.ocr_rules import Line, parse, rows


def line(text: str, y: float = 0, x: float = 0) -> Line:
    return Line(text, 0.9, ((x, y), (x + 100, y), (x + 100, y + 10), (x, y + 10)))


def test_geometric_reading_order() -> None:
    assert rows([line("100", 0, 200), line("TOTAL"), line("CASH", 30)]) == ["TOTAL 100", "CASH"]


def test_subtotal_and_grand_total_have_distinct_meaning() -> None:
    raw, _ = parse(
        [line("SUBTOTAL 10,000"), line("TOTAL 10,000", 30), line("GRAND TOTAL 11,000", 60)],
        "synthetic",
    )
    assert raw.subtotal == "10,000"
    assert raw.total == "11,000"


def test_conflicting_total_candidates_abstain() -> None:
    raw, evidence = parse([line("TOTAL 10,000"), line("TOTAL 11,000", 30)], "fixture")
    assert raw.total is None
    assert evidence["total"] is not None


def test_percent_is_not_tax_amount() -> None:
    raw, _ = parse([line("TAX 10%")], "fixture")
    assert raw.tax is None
    raw, _ = parse([line("TAX 10% 1,000")], "fixture")
    assert raw.tax == "1,000"


def test_missing_fields_stay_missing_and_items_incomplete() -> None:
    raw, _ = parse([line("TOTAL 1,000")], "fixture")
    assert raw.tax is None and raw.discount is None
    assert raw.items_complete is False
    assert raw.currency is None


def test_only_explicit_item_layout_is_supported() -> None:
    raw, _ = parse(
        [line("2x Tea 20,000"), line("CASH 50,000", 30), line("TEL 12345678", 60)], "fixture"
    )
    assert len(raw.items) == 1
    assert raw.items[0].quantity == "2x"
    assert raw.items[0].description == "Tea"
    assert raw.items[0].unit_price is None


def test_empty_ocr_does_not_invent_a_receipt() -> None:
    raw, _ = parse([], "fixture")
    assert not raw.items and raw.total is None
