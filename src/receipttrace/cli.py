"""Local acquisition, validation, image extraction and independent evaluation commands."""

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import cast
from urllib.error import URLError

from receipttrace.cli_serialization import decimal_json
from receipttrace.data import (
    DATASET,
    EXPECTED_SHA256,
    REVISION,
    SHARD,
    SOURCE_URL,
    acquire,
    inspect,
    verify,
    write_json,
)
from receipttrace.domain import RawReceipt, report
from receipttrace.money import POLICIES, NumberPolicy


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare-cord", help="Download ~490 MB and inspect train shard 0")
    prepare.add_argument("--size", type=int, default=20)
    prepare.add_argument("--seed", type=int, default=42)
    prepare.add_argument("--output", type=Path, default=Path("data/processed/cord-inspection"))
    check = commands.add_parser("verify-sample", help="Verify image and label checksums offline")
    check.add_argument("--output", type=Path, default=Path("data/processed/cord-inspection"))
    validation = commands.add_parser("validate-receipt", help="Validate structured receipt text")
    validation.add_argument("input", type=Path)
    validation.add_argument("--policy", choices=POLICIES, required=True)
    validation.add_argument("--tolerance", default="0")
    ocr = commands.add_parser("extract-ocr", help="Run local CPU OCR on PNG images only")
    ocr.add_argument("--inputs", type=Path, required=True)
    ocr.add_argument("--output", type=Path, required=True)
    evaluation = commands.add_parser(
        "evaluate-extraction",
        aliases=["evaluate-ocr"],
        help="Compare a saved run with CORD annotations",
    )
    evaluation.add_argument("--sample", type=Path, required=True)
    evaluation.add_argument("--run", type=Path, required=True)
    evaluation.add_argument("--output", type=Path, required=True)
    for name in ("plan-llm", "extract-llm"):
        llm = commands.add_parser(
            name, help="Plan offline or execute explicitly budgeted vision extraction"
        )
        llm.add_argument("--inputs", type=Path, required=True)
        llm.add_argument("--config", type=Path, required=True)
        llm.add_argument("--output", type=Path, required=True)
    comparison = commands.add_parser(
        "compare-extractions", help="Compare evaluations of the same sample"
    )
    comparison.add_argument("--baseline", type=Path, required=True)
    comparison.add_argument("--candidate", type=Path, required=True)
    comparison.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "compare-extractions":
            from receipttrace.evaluation import compare_reports

            compare_reports(args.baseline, args.candidate, args.output)
            print("Comparison saved")
            return 0
        if args.command in ("plan-llm", "extract-llm"):
            from receipttrace.llm import plan
            from receipttrace.llm import run as llm_run
            from receipttrace.llm_config import LLMConfig

            config = LLMConfig.model_validate_json(args.config.read_bytes())
            if args.command == "plan-llm":
                if args.output.exists():
                    raise FileExistsError("Output already exists")
                prepared = plan(args.inputs, config)
                args.output.parent.mkdir(parents=True, exist_ok=True)
                write_json(args.output, prepared)
                print(f"Offline plan: {len(prepared['documents'])} images; no API calls")
                return 0
            result = llm_run(args.inputs, args.output, config)
            return 2 if any(row["status"] == "error" for row in result["records"]) else 0
        if args.command in ("evaluate-ocr", "evaluate-extraction"):
            from receipttrace.evaluation import evaluate

            result = evaluate(args.sample, args.run, args.output)
            print(json.dumps({"documents": result["document_count"], "metrics": result["metrics"]}))
            return 0
        if args.command == "extract-ocr":
            from receipttrace.ocr import run

            result = run(args.inputs, args.output)
            return 2 if any(row["status"] == "error" for row in result["records"]) else 0
        if args.command == "validate-receipt":
            payload = args.input.read_bytes()
            raw = RawReceipt.model_validate_json(payload)
            result = report(raw, cast(NumberPolicy, args.policy), Decimal(args.tolerance))
            result["input_sha256"] = hashlib.sha256(payload).hexdigest()
            print(json.dumps(result, ensure_ascii=False, indent=2, default=decimal_json))
            return 2 if result["has_findings"] else 0
        if args.command == "verify-sample":
            print(f"Verified {verify(args.output)} documents")
            return 0
        if args.size < 1:
            raise ValueError("Sample size must be positive")
        if args.output.exists():
            raise FileExistsError(f"Output already exists: {args.output}")
        source = Path("data/raw/cord") / Path(SHARD).name
        downloaded = not source.exists()
        print("Acquiring pinned CORD train shard (~490 MB); verifying SHA-256...", flush=True)
        acquire(source)
        download_record = source.parent / "download.json"
        if downloaded or not download_record.exists():
            write_json(
                download_record,
                {
                    "dataset": DATASET,
                    "revision": REVISION,
                    "source_url": SOURCE_URL,
                    "sha256": EXPECTED_SHA256,
                    "bytes": source.stat().st_size,
                    "verified_at_utc": datetime.now(UTC).isoformat(),
                    "downloaded_in_this_run": downloaded,
                    "acquired_at_utc": datetime.now(UTC).isoformat() if downloaded else None,
                    "license": "CC-BY-4.0",
                },
            )
        manifest = inspect(source, args.output, args.size, args.seed)
        print(json.dumps({"sample_size": manifest["sample_size"], "output": str(args.output)}))
        return 0
    except (OSError, ValueError, URLError, InvalidOperation, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
