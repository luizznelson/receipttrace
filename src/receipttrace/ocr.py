"""Image-only OCR execution. This module never opens reference annotations."""

import json
import platform
import subprocess
import time
from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal
from importlib.metadata import distribution, version
from pathlib import Path
from typing import Any

from receipttrace.cli_serialization import decimal_json
from receipttrace.data import sha256
from receipttrace.domain import report
from receipttrace.ocr_rules import Line, parse


class Engine:
    def __init__(self) -> None:
        try:
            from rapidocr import RapidOCR
        except ImportError as error:
            raise RuntimeError(
                "Install OCR dependencies with uv sync --locked --extra ocr"
            ) from error
        package = Path(str(distribution("rapidocr").locate_file("rapidocr")))
        models = {
            "Det": package / "models/PP-OCRv6_det_small.onnx",
            "Cls": package / "models/ch_ppocr_mobile_v2.0_cls_mobile.onnx",
            "Rec": package / "models/PP-OCRv6_rec_small.onnx",
        }
        params: dict[str, Any] = {
            "EngineConfig.onnxruntime.intra_op_num_threads": 1,
            "EngineConfig.onnxruntime.inter_op_num_threads": 1,
            "Global.log_level": "warning",
        }
        params.update({f"{name}.model_path": str(path) for name, path in models.items()})
        self.metadata = {
            "rapidocr": version("rapidocr"),
            "onnxruntime": version("onnxruntime"),
            "config_sha256": sha256(package / "config.yaml"),
            "models": {
                name: {"file": path.name, "sha256": sha256(path)} for name, path in models.items()
            },
            "threads": 1,
            "provider": "CPU",
            "text_score": 0.5,
        }
        self.engine = RapidOCR(params=params)

    def read(self, path: Path) -> list[Line]:
        return self.read_image(str(path))

    def read_image(self, image: str | bytes) -> list[Line]:
        from rapidocr.utils.output import RapidOCROutput

        result = self.engine(image)
        if not isinstance(result, RapidOCROutput):
            raise ValueError("Expected complete detection/classification/recognition output")
        if result.txts is None:
            return []
        if result.boxes is None or result.scores is None:
            raise ValueError("OCR returned texts without coordinates or scores")
        return [
            Line(str(text), float(score), tuple((float(p[0]), float(p[1])) for p in box))
            for text, score, box in zip(result.txts, result.scores, result.boxes, strict=True)
        ]


def run(inputs: Path, output: Path) -> dict[str, Any]:
    images = sorted(inputs.glob("*.png"))
    if not images:
        raise ValueError("Input directory contains no PNG images")
    if output.exists():
        raise FileExistsError(f"Output already exists: {output}")
    initialized = time.perf_counter()
    engine = Engine()
    initialization = time.perf_counter() - initialized
    output.mkdir(parents=True)
    records: list[dict[str, Any]] = []
    for image in images:
        started = time.perf_counter()
        record: dict[str, Any] = {"id": image.stem, "image_sha256": sha256(image)}
        try:
            lines = engine.read(image)
            raw, evidence = parse(lines, image.stem)
            record.update(
                {
                    "status": "ok" if lines else "empty",
                    "lines": [asdict(line) for line in lines],
                    "evidence": evidence,
                    "validation": report(raw, "idr-grouped", Decimal(0)),
                }
            )
        except Exception as error:
            # Batch boundary: preserve failures in the denominator and continue other documents.
            record.update(
                {"status": "error", "error_type": type(error).__name__, "error": str(error)}
            )
        record["seconds"] = time.perf_counter() - started
        path = output / f"{image.stem}.json"
        path.write_text(
            json.dumps(record, ensure_ascii=False, indent=2, default=decimal_json) + "\n",
            encoding="utf-8",
        )
        records.append(
            {
                "id": image.stem,
                "file": path.name,
                "sha256": sha256(path),
                "status": record["status"],
                "seconds": record["seconds"],
            }
        )
        print(f"{image.stem}: {record['status']}", flush=True)
    git = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
    dirty = subprocess.run(
        ["git", "status", "--porcelain"], capture_output=True, text=True, check=False
    )
    manifest = {
        "schema_version": 1,
        "rules_version": "ocr-rules-1",
        "engine": engine.metadata,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "initialization_seconds": initialization,
        "latency_scope": "hash + OCR + parsing + validation; excludes init and output IO",
        "cache": "none",
        "git_commit": git.stdout.strip() if git.returncode == 0 else None,
        "git_dirty": bool(dirty.stdout) if dirty.returncode == 0 else None,
        "source_hashes": {str(path): sha256(path) for path in sorted(Path("src").rglob("*.py"))},
        "lock_sha256": sha256(Path("uv.lock")),
        "records": records,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
