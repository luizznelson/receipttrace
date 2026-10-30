"""Verified, packaged public examples; never performs inference or reads credentials."""

import hashlib
import json
from pathlib import Path
from typing import Any, Literal

from receipttrace.domain import RawReceipt, report, summarize_validation

Method = Literal["ocr", "gemini"]
EXAMPLE_IDS = tuple(f"cord-train-shard0-row{row:04d}" for row in (6, 59, 173))
REPORT_NAMES = {"ocr": "ocr-baseline.json", "gemini": "gemini-development-20.json"}


class ExampleNotFound(ValueError):
    """Only known public examples may be opened through the web application."""


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class DemoCatalog:
    def __init__(self, root: Path) -> None:
        self.root = root
        checksums = json.loads((root / "checksums.json").read_bytes())
        for name, expected in checksums.items():
            path = (root / name).resolve()
            if not path.is_relative_to(root.resolve()) or digest(path) != expected:
                raise ValueError("Bundled demonstration evidence failed integrity verification")
        self.reports = {
            key: json.loads((root / "reports" / name).read_bytes())
            for key, name in REPORT_NAMES.items()
        }
        before, after = self.reports["ocr"], self.reports["gemini"]
        if (
            before["sample_manifest_sha256"] != after["sample_manifest_sha256"]
            or before["document_count"] != after["document_count"]
            or before["evaluation_version"] != after["evaluation_version"]
        ):
            raise ValueError("Bundled evaluations do not describe the same sample")
        self.manifest = json.loads((root / "reports/cord-inspection.manifest.json").read_bytes())
        if (
            digest(root / "reports/cord-inspection.manifest.json")
            != after["sample_manifest_sha256"]
        ):
            raise ValueError("Sample manifest does not match the evaluation")
        for method, evaluation in self.reports.items():
            if digest(self.run(method) / "manifest.json") != evaluation["run_manifest_sha256"]:
                raise ValueError("Extraction manifest does not match the evaluation")
        for document_id in EXAMPLE_IDS:
            image_record = next(row for row in self.manifest["records"] if row["id"] == document_id)
            if digest(self.image(document_id)) != image_record["image_sha256"]:
                raise ValueError("Example image does not match the sample")

    def run(self, method: str) -> Path:
        if method not in REPORT_NAMES:
            raise ExampleNotFound("Unknown extraction method")
        return self.root / "extractions" / method

    @staticmethod
    def require_example(document_id: str) -> None:
        if document_id not in EXAMPLE_IDS:
            raise ExampleNotFound("Unknown public example")

    def image(self, document_id: str) -> Path:
        self.require_example(document_id)
        return self.root / "images" / (document_id + ".png")

    def summary(self) -> dict[str, Any]:
        after, before = self.reports["gemini"], self.reports["ocr"]
        return {
            "document_count": after["document_count"],
            "example_count": len(EXAMPLE_IDS),
            "scope": "development_training_sample",
            "curated_examples": True,
            "total_gain": after["metrics"]["total"]["correct"]
            - before["metrics"]["total"]["correct"],
            "methods": {
                name: {
                    key: data.get(key) for key in ("metrics", "latency", "statuses", "cost_summary")
                }
                for name, data in self.reports.items()
            },
            "dataset": self.manifest["dataset"],
            "dataset_revision": self.manifest["revision"],
            "license": "CC-BY-4.0",
        }

    def examples(self) -> list[dict[str, str]]:
        return [
            {
                "id": document_id,
                "title_key": f"case_{index}",
                "image_url": f"/api/examples/{document_id}/image",
            }
            for index, document_id in enumerate(EXAMPLE_IDS, start=1)
        ]

    def detail(self, document_id: str, method: Method) -> dict[str, Any]:
        from decimal import Decimal

        self.require_example(document_id)
        folder = self.run(method)
        manifest_path = folder / "manifest.json"
        manifest = json.loads(manifest_path.read_bytes())
        record = next(row for row in manifest["records"] if row["id"] == document_id)
        result_path = folder / record["file"]
        if (
            not result_path.resolve().is_relative_to(folder.resolve())
            or digest(result_path) != record["sha256"]
        ):
            raise ValueError("Example result checksum mismatch")
        result = json.loads(result_path.read_bytes())
        source = next(row for row in self.manifest["records"] if row["id"] == document_id)
        if result["id"] != document_id or result["image_sha256"] != source["image_sha256"]:
            raise ValueError("Example result does not match the source image")
        evaluation = next(
            row for row in self.reports[method]["documents"] if row["id"] == document_id
        )
        original = result.get("validation")
        validation = (
            report(
                RawReceipt.model_validate(original["raw"]),
                original["numeric_policy"],
                Decimal(original["tolerance"]),
            )
            if original is not None
            else None
        )
        return {
            "id": document_id,
            "method": method,
            "image_url": f"/api/examples/{document_id}/image",
            "extraction_status": result["status"],
            "seconds": result["seconds"],
            "raw": validation["raw"] if validation else None,
            "validation": validation,
            "arithmetic": summarize_validation(validation),
            "evaluation": evaluation["fields"],
            "source": {
                "image_sha256": result["image_sha256"],
                "result_sha256": record["sha256"],
                "run_manifest_sha256": digest(manifest_path),
                "evaluation_sha256": digest(self.root / "reports" / REPORT_NAMES[method]),
            },
        }
