"""Local data preparation commands. No extraction or benchmark is claimed here."""

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import cast
from urllib.error import URLError

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


def decimal_json(value: object) -> str:
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"Unsupported JSON type: {type(value).__name__}")


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
    args = parser.parse_args()
    try:
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
    except (OSError, ValueError, URLError, InvalidOperation) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
