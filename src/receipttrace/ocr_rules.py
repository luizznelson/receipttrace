"""Deterministic, intentionally limited rules over OCR text and coordinates."""

import re
from dataclasses import dataclass

from receipttrace.domain import RawItem, RawReceipt
from receipttrace.money import money, quantity


@dataclass(frozen=True)
class Line:
    text: str
    score: float
    box: tuple[tuple[float, float], ...]

    @property
    def y(self) -> float:
        return sum(point[1] for point in self.box) / len(self.box)

    @property
    def height(self) -> float:
        return max(point[1] for point in self.box) - min(point[1] for point in self.box)


def rows(lines: list[Line]) -> list[str]:
    groups: list[list[Line]] = []
    for line in sorted(lines, key=lambda value: value.y):
        if not groups or abs(line.y - groups[-1][0].y) > max(4, line.height * 0.45):
            groups.append([line])
        else:
            groups[-1].append(line)
    return [
        " ".join(line.text for line in sorted(group, key=lambda value: value.box[0][0]))
        for group in groups
    ]


def parse(lines: list[Line], document_id: str) -> tuple[RawReceipt, dict[str, object]]:
    grouped = rows(lines)
    candidates: dict[str, list[tuple[int, str, str]]] = {}
    items: list[RawItem] = []
    evidence: dict[str, object] = {"rows": grouped, "item_rows": []}
    item_rows: list[str] = []
    number = re.compile(r"(?<![A-Za-z0-9])(?:Rp\.?\s*)?-?[0-9]+(?:[.,][0-9]+)*")
    for row in grouped:
        upper = row.upper()
        tokens = [
            match
            for match in number.finditer(row)
            if not row[match.end() :].lstrip().startswith("%")
        ]
        amount = tokens[-1].group().strip() if tokens else None
        if amount is None or money(amount, "idr-grouped", signed=True).status != "parsed":
            continue
        field: str | None = None
        priority = 1
        if re.search(r"\b(?:SUB\s*TOTAL|SUBTOTAL)\b", upper):
            field = "subtotal"
        elif re.search(r"\b(?:GRAND\s*TOTAL|TOTAL\s*(?:BAYAR|PAYMENT))\b", upper):
            field, priority = "total", 2
        elif re.search(r"\bTOTAL\b", upper) and not re.search(r"ITEM|QTY", upper):
            field = "total"
        elif re.search(r"\b(?:TAX|PPN|PAJAK)\b", upper):
            field = "tax"
        elif re.search(r"\b(?:SERVICE|SERVIS)\b", upper):
            field = "service"
        elif re.search(r"\b(?:DISCOUNT|DISC|DISKON)\b", upper):
            field = "discount"
        if field is not None:
            candidates.setdefault(field, []).append((priority, amount, row))
            continue
        # Only explicit leading quantity + description + terminal amount is supported.
        # This avoids treating every merchant/address line as an item.
        if re.search(r"CASH|CHANGE|TUNAI|KEMBALI|ITEMS|DATE|TEL|CARD|CREDIT", upper):
            continue
        item_match = re.fullmatch(
            r"\s*([0-9]+(?:\.[0-9]+)?\s*[xX]?)\s+([A-Za-z].*?)\s+"
            r"((?:Rp\.?\s*)?[0-9]+(?:[.,][0-9]+)*)\s*",
            row,
        )
        if item_match and quantity(item_match.group(1)).status == "parsed":
            items.append(
                RawItem(
                    description=item_match.group(2),
                    quantity=item_match.group(1),
                    amount=item_match.group(3),
                )
            )
            item_rows.append(row)
    fields: dict[str, str | None] = {}
    for name, choices in candidates.items():
        highest = max(choice[0] for choice in choices)
        preferred = [choice for choice in choices if choice[0] == highest]
        values = {
            money(choice[1], "idr-grouped", signed=name == "discount").value for choice in preferred
        }
        fields[name] = preferred[0][1] if len(values) == 1 else None
        evidence[name] = {"candidates": preferred, "ambiguous": len(values) != 1}
    evidence["item_rows"] = item_rows
    raw = RawReceipt(document_id=document_id, items=items, items_complete=False, **fields)
    return raw, evidence
