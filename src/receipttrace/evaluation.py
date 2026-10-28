"""Independent field evaluation; annotations are never passed to the OCR engine."""

import json
import math
from pathlib import Path
from typing import Any

from receipttrace.data import sha256, verify, write_json
from receipttrace.money import money

FIELDS = {
    "total": ("total", "total_price"),
    "subtotal": ("sub_total", "subtotal_price"),
    "tax": ("sub_total", "tax_price"),
    "service": ("sub_total", "service_price"),
    "discount": ("sub_total", "discount_price"),
}


def field_result(expected: str | None, predicted: str | None, *, signed: bool = False) -> str:
    reference = money(expected, "idr-grouped", signed=signed)
    guess = money(predicted, "idr-grouped", signed=signed)
    if reference.status == "invalid":
        return "invalid_reference"
    if reference.value is None:
        return "unannotated_prediction" if predicted is not None else "unannotated_abstention"
    if guess.value is None:
        return "missed"
    a = abs(reference.value) if signed else reference.value
    b = abs(guess.value) if signed else guess.value
    return "correct" if a == b else "wrong_value"


def safe_path(base: Path, name: str) -> Path:
    path = (base / name).resolve()
    if not path.is_relative_to(base.resolve()):
        raise ValueError("Manifest path escapes its directory")
    return path


def evaluate(sample: Path, run: Path, output: Path) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError(f"Output already exists: {output}")
    verify(sample)
    sample_manifest = json.loads((sample / "manifest.json").read_text(encoding="utf-8"))
    run_manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    run_records = {row["id"]: row for row in run_manifest["records"]}
    sample_records = {row["id"]: row for row in sample_manifest["records"]}
    if (
        len(run_records) != len(run_manifest["records"])
        or len(sample_records) != len(sample_manifest["records"])
        or set(run_records) != set(sample_records)
    ):
        raise ValueError("Sample/run document IDs must match exactly without duplicates")
    results: list[dict[str, Any]] = []
    counts = {
        field: {
            status: 0
            for status in (
                "correct",
                "wrong_value",
                "missed",
                "invalid_reference",
                "unannotated_prediction",
                "unannotated_abstention",
            )
        }
        for field in FIELDS
    }
    latencies: list[float] = []
    statuses = {"ok": 0, "empty": 0, "error": 0}
    for document_id, source in sample_records.items():
        record = run_records[document_id]
        path = safe_path(run, record["file"])
        if sha256(path) != record["sha256"]:
            raise ValueError(f"Result checksum mismatch: {document_id}")
        prediction = json.loads(path.read_text(encoding="utf-8"))
        if prediction["id"] != document_id or prediction["image_sha256"] != source["image_sha256"]:
            raise ValueError(f"Prediction/source mismatch: {document_id}")
        if prediction["status"] != record["status"] or record["status"] not in statuses:
            raise ValueError("Invalid prediction status")
        statuses[prediction["status"]] += 1
        seconds = float(prediction["seconds"])
        if not math.isfinite(seconds) or seconds < 0:
            raise ValueError("Invalid latency")
        latencies.append(seconds)
        truth = json.loads(safe_path(sample, source["reference"]).read_text(encoding="utf-8"))
        actual = prediction.get("validation", {}).get("raw", {})
        field_details = {}
        for field, (section, key) in FIELDS.items():
            expected = truth["gt_parse"].get(section, {}).get(key)
            guessed = actual.get(field)
            outcome = field_result(expected, guessed, signed=field == "discount")
            counts[field][outcome] += 1
            field_details[field] = {"expected": expected, "predicted": guessed, "outcome": outcome}
        results.append(
            {
                "id": document_id,
                "image_sha256": source["image_sha256"],
                "result_sha256": record["sha256"],
                "status": prediction["status"],
                "seconds": seconds,
                "fields": field_details,
            }
        )
    metrics = {}
    for field, count in counts.items():
        annotated = count["correct"] + count["wrong_value"] + count["missed"]
        answered = count["correct"] + count["wrong_value"]
        metrics[field] = {
            **count,
            "annotated_documents": annotated,
            "exact_match_recall": count["correct"] / annotated if annotated else None,
            "precision_on_annotated_answers": count["correct"] / answered if answered else None,
        }
    ordered = sorted(latencies)
    if not ordered:
        raise ValueError("Cannot evaluate an empty sample")
    result = {
        "evaluation_version": "1",
        "scope": "development sample, first CORD training shard",
        "sample_manifest_sha256": sha256(sample / "manifest.json"),
        "run_manifest_sha256": sha256(run / "manifest.json"),
        "document_count": len(results),
        "engine": run_manifest["engine"],
        "run_git_commit": run_manifest["git_commit"],
        "run_git_dirty": run_manifest["git_dirty"],
        "source_hashes": run_manifest["source_hashes"],
        "lock_sha256": run_manifest["lock_sha256"],
        "statuses": statuses,
        "metrics": metrics,
        "latency": {
            "p50_seconds": ordered[math.ceil(0.5 * len(ordered)) - 1],
            "p95_seconds": ordered[math.ceil(0.95 * len(ordered)) - 1],
            "method": "nearest rank, includes first lazy inference; excludes engine init",
            "initialization_seconds": run_manifest["initialization_seconds"],
        },
        "limitations": [
            "No item matching metrics yet",
            "Unannotated fields are not negatives",
            "Not a held-out benchmark",
            "OCR scores are not calibrated probabilities",
            "No paid inference; CPU and hosting resource cost not estimated",
        ],
        "documents": results,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    write_json(output, result)
    return result
