"""Offline integration: image-only extraction, failure accounting and integrity checks."""

import json
from pathlib import Path

import pytest

from receipttrace import ocr
from receipttrace.data import sha256, write_json
from receipttrace.evaluation import evaluate
from receipttrace.ocr_rules import Line


def test_failed_document_remains_in_evaluation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sample = tmp_path / "sample"
    inputs = sample / "inputs"
    refs = sample / "reference"
    inputs.mkdir(parents=True)
    refs.mkdir()
    records = []
    for name in ["a", "b"]:
        image = inputs / f"{name}.png"
        image.write_bytes(b"synthetic-image-fixture")
        reference = refs / f"{name}.json"
        write_json(reference, {"gt_parse": {"total": {"total_price": "1,000"}}})
        records.append(
            {
                "id": name,
                "image": f"inputs/{name}.png",
                "image_sha256": sha256(image),
                "reference": f"reference/{name}.json",
                "reference_sha256": sha256(reference),
            }
        )
    write_json(sample / "manifest.json", {"records": records})

    class FakeEngine:
        metadata = {"kind": "synthetic-test-engine-not-real-OCR"}

        def read(self, path: Path) -> list[Line]:
            assert path.parent == inputs
            if path.stem == "b":
                raise RuntimeError("simulated inference failure")
            return [Line("TOTAL 1,000", 0.9, ((0, 0), (100, 0), (100, 10), (0, 10)))]

    monkeypatch.setattr(ocr, "Engine", FakeEngine)
    run = tmp_path / "run"
    ocr.run(inputs, run)
    result = evaluate(sample, run, tmp_path / "evaluation.json")
    assert result["document_count"] == 2
    assert result["statuses"] == {"ok": 1, "empty": 0, "error": 1}
    assert result["metrics"]["total"]["exact_match_recall"] == 0.5
    assert result["metrics"]["total"]["missed"] == 1
    assert result["metrics"]["tax"]["exact_match_recall"] is None
    manifest = json.loads((run / "manifest.json").read_text())
    assert manifest["records"][1]["status"] == "error"
    (run / "a.json").write_text("{}")
    with pytest.raises(ValueError, match="checksum mismatch"):
        evaluate(sample, run, tmp_path / "tampered.json")


def test_run_rejects_empty_input_directory(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="no PNG"):
        ocr.run(tmp_path, tmp_path / "output")
