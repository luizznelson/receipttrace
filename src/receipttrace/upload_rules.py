"""Conservative live-upload rules, separate from the frozen CORD baseline."""

import re
import unicodedata
from typing import Any

from receipttrace.domain import RawReceipt
from receipttrace.money import NumberPolicy, money
from receipttrace.ocr_rules import Line, rows

RULES_VERSION = "upload-rules-1"
NUMBER = re.compile(r"(?<![\w.,])(?:R\$\s*|\$\s*|Rp\.?\s*)?-?\d+(?:[.,]\d+)*")


def parse_upload(
    lines: list[Line], document_id: str, policy: NumberPolicy
) -> tuple[RawReceipt, dict[str, Any]]:
    grouped = rows(lines)
    candidates: dict[str, list[dict[str, Any]]] = {}
    for index, row in enumerate(grouped):
        label = "".join(
            c for c in unicodedata.normalize("NFD", row.upper()) if not unicodedata.combining(c)
        )
        if re.search(r"\b(?:TROCO|CHANGE|CASH|TUNAI|KEMBALI|PAGAMENTO|PAYMENT|CARTAO)\b", label):
            if not re.search(r"\bTOTAL\s+(?:A\s+PAGAR|PAYMENT)\b", label):
                continue
        name, priority = None, 1
        if re.search(r"\bSUB\s*TOTAL\b", label):
            name = "subtotal"
        elif re.search(
            r"\b(?:GRAND\s+TOTAL|TOTAL\s+A\s+PAGAR|VALOR\s+(?:TOTAL|A\s+PAGAR))\b", label
        ):
            name, priority = "total", 2
        elif re.search(r"\bTOTAL\b", label) and not re.search(
            r"\b(?:ITENS|ITEMS|QTD|QTY)\b", label
        ):
            name = "total"
        elif re.search(r"\b(?:IMPOSTO|IMPOSTOS|TAX|PPN|PAJAK)\b", label):
            name = "tax"
        elif re.search(r"\b(?:SERVICO|SERVICE|SERVIS)\b", label):
            name = "service"
        elif re.search(r"\b(?:DESCONTO|DISCOUNT|DISKON)\b", label):
            name = "discount"
        if name is None:
            continue
        tokens = [
            match.group().strip()
            for match in NUMBER.finditer(row)
            if not row[match.end() :].lstrip().startswith("%")
        ]
        if not tokens or money(tokens[-1], policy, signed=name == "discount").status != "parsed":
            continue
        candidates.setdefault(name, []).append(
            {"row": index, "text": row, "value": tokens[-1], "priority": priority}
        )
    fields: dict[str, str | None] = {}
    evidence: dict[str, Any] = {}
    for name, options in candidates.items():
        highest = max(option["priority"] for option in options)
        preferred = [option for option in options if option["priority"] == highest]
        values = {
            money(option["value"], policy, signed=name == "discount").value for option in preferred
        }
        ambiguous = len(values) != 1
        fields[name] = None if ambiguous else preferred[0]["value"]
        evidence[name] = {"candidates": options, "ambiguous": ambiguous}
    return RawReceipt.model_validate({"document_id": document_id, **fields}), {
        "rows": grouped,
        "fields": evidence,
    }
