"""Exercise CLI contracts, audit metadata and error exit codes without network."""

import hashlib
import json
from pathlib import Path

import pytest

from receipttrace.cli import main


def payload() -> dict[str, object]:
    return {
        "document_id": "synthetic-cli-case",
        "subtotal": "0.30",
        "discount": "0",
        "tax": "0",
        "service": "0",
        "total": "0.30",
    }


def test_cli_serializes_decimal_and_preserves_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "receipt.json"
    original = json.dumps(payload()).encode()
    source.write_bytes(original)
    monkeypatch.setattr(
        "sys.argv", ["receipttrace", "validate-receipt", str(source), "--policy", "decimal-dot"]
    )
    assert main() == 0
    result = json.loads(capsys.readouterr().out)
    assert result["input_sha256"] == hashlib.sha256(original).hexdigest()
    assert result["normalized"]["total"]["value"] == "0.30"
    assert result["checks"][-1]["status"] == "pass"
    assert result["has_skipped_checks"] is True
    assert source.read_bytes() == original


@pytest.mark.parametrize("total", ["0.31", "unknown", "-1"])
def test_cli_findings_exit_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], total: str
) -> None:
    source = tmp_path / "receipt.json"
    data = payload()
    data["total"] = total
    source.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv", ["receipttrace", "validate-receipt", str(source), "--policy", "decimal-dot"]
    )
    assert main() == 2
    assert json.loads(capsys.readouterr().out)["has_findings"] is True


@pytest.mark.parametrize("text", ["not json", '{"document_id":"fixture","total":0.1}'])
def test_cli_rejects_invalid_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], text: str
) -> None:
    source = tmp_path / "receipt.json"
    source.write_text(text, encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv", ["receipttrace", "validate-receipt", str(source), "--policy", "decimal-dot"]
    )
    assert main() == 1
    assert "Error:" in capsys.readouterr().err


@pytest.mark.parametrize("tolerance", ["NaN", "-0.01", "not-a-number"])
def test_cli_rejects_invalid_tolerance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tolerance: str,
) -> None:
    source = tmp_path / "receipt.json"
    source.write_text(json.dumps(payload()), encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        [
            "receipttrace",
            "validate-receipt",
            str(source),
            "--policy",
            "decimal-dot",
            "--tolerance",
            tolerance,
        ],
    )
    assert main() == 1
    assert "Error:" in capsys.readouterr().err
