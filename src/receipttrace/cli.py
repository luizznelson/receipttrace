"""Local data preparation commands. No extraction or benchmark is claimed here."""

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare-cord", help="Download ~490 MB and inspect train shard 0")
    prepare.add_argument("--size", type=int, default=20)
    prepare.add_argument("--seed", type=int, default=42)
    prepare.add_argument("--output", type=Path, default=Path("data/processed/cord-inspection"))
    check = commands.add_parser("verify-sample", help="Verify image and label checksums offline")
    check.add_argument("--output", type=Path, default=Path("data/processed/cord-inspection"))
    args = parser.parse_args()
    try:
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
    except (OSError, ValueError, URLError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
