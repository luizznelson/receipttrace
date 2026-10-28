"""Acquire a pinned development shard and prepare a verifiable inspection sample."""

import hashlib
import json
import random
import shutil
import tempfile
from collections import Counter
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.request import urlopen

import pyarrow.parquet as pq
from PIL import Image

DATASET = "naver-clova-ix/cord-v2"
REVISION = "7f0115a4b758a71d6473b8d085751692da2fef98"
SHARD = "data/train-00000-of-00004-b4aaeceff1d90ecb.parquet"
EXPECTED_SHA256 = "da3994eee1bf9bd3c57f0d53a72c3a6812c8696c5ba26245987949ddf73483cc"
SOURCE_URL = f"https://huggingface.co/datasets/{DATASET}/resolve/{REVISION}/{SHARD}"


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def select_indices(population: int, size: int, seed: int) -> list[int]:
    if not 1 <= size <= population:
        raise ValueError(f"Sample size must be between 1 and {population}")
    return sorted(random.Random(seed).sample(range(population), size))


def acquire(destination: Path, url: str = SOURCE_URL, expected: str = EXPECTED_SHA256) -> Path:
    """Verify cached files and only publish complete, checksum-verified downloads."""
    if destination.exists():
        if sha256(destination) != expected:
            raise ValueError(f"Checksum mismatch: {destination}; remove corrupt file to retry")
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as output:
            temporary = Path(output.name)
            with urlopen(url, timeout=120) as response:  # noqa: S310
                shutil.copyfileobj(response, output, length=1024 * 1024)
        if sha256(temporary) != expected:
            raise ValueError("Downloaded file does not match the pinned source checksum")
        temporary.replace(destination)
        return destination
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def inspect(source: Path, output: Path, size: int = 20, seed: int = 42) -> dict[str, Any]:
    """Keep labels outside the image-only input directory. Never mutate the source."""
    if sha256(source) != EXPECTED_SHA256:
        raise ValueError("Inspection requires the verified, pinned CORD shard")
    parquet = pq.ParquetFile(source)
    selected = select_indices(parquet.metadata.num_rows, size, seed)
    if output.exists():
        raise FileExistsError(f"Output already exists: {output}; use a new directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".inspection-", dir=output.parent))
    try:
        images = staging / "inputs"
        labels = staging / "reference"
        images.mkdir()
        labels.mkdir()
        records: list[dict[str, Any]] = []
        fields: Counter[str] = Counter()
        image_hashes: list[str] = []
        offset = 0
        for batch in parquet.iter_batches(batch_size=1, columns=["image", "ground_truth"]):
            if offset in selected:
                row = batch.to_pylist()[0]
                image_bytes = row["image"]["bytes"]
                truth = json.loads(row["ground_truth"])
                if not isinstance(truth, dict) or not isinstance(truth.get("gt_parse"), dict):
                    raise ValueError(f"Missing or invalid gt_parse at row {offset}")
                parsed = truth["gt_parse"]
                document_id = f"cord-train-shard0-row{offset:04d}"
                image_path = images / f"{document_id}.png"
                with Image.open(BytesIO(image_bytes)) as image:
                    image.verify()
                # Preserve original bytes; confirm the source actually encodes PNG.
                with Image.open(BytesIO(image_bytes)) as image:
                    if image.format != "PNG":
                        raise ValueError("Unexpected source image format")
                    dimensions = list(image.size)
                image_path.write_bytes(image_bytes)
                label_path = labels / f"{document_id}.json"
                write_json(label_path, truth)
                menu = parsed.get("menu", [])
                items = [menu] if isinstance(menu, dict) else menu
                for field in ("nm", "cnt", "unitprice", "price"):
                    fields[f"items.{field}"] += sum(field in item for item in items)
                fields["items.total"] += len(items)
                fields["documents.total_price"] += "total_price" in parsed.get("total", {})
                fields["documents.subtotal"] += "subtotal_price" in parsed.get("sub_total", {})
                image_hash = sha256(image_path)
                image_hashes.append(image_hash)
                records.append(
                    {
                        "id": document_id,
                        "source_row": offset,
                        "source_image_id": truth.get("meta", {}).get("image_id"),
                        "image": f"inputs/{image_path.name}",
                        "image_sha256": image_hash,
                        "reference": f"reference/{label_path.name}",
                        "reference_sha256": sha256(label_path),
                        "dimensions": dimensions,
                        "item_count": len(items),
                    }
                )
            offset += 1
        manifest = {
            "schema_version": 1,
            "dataset": DATASET,
            "revision": REVISION,
            "source_url": SOURCE_URL,
            "source_sha256": EXPECTED_SHA256,
            "source_bytes": source.stat().st_size,
            "license": "CC-BY-4.0",
            "prepared_at_utc": datetime.now(UTC).isoformat(),
            "source_download_record": "data/raw/cord/download.json",
            "split": "train",
            "shard": SHARD,
            "population_rows": offset,
            "sample_size": size,
            "seed": seed,
            "selected_indices": selected,
            "sampling_scope": "first training shard only; not representative of all CORD",
            "image_transformations": "none; original encoded bytes",
            "reference_transformations": "JSON reserialization; semantic content preserved",
            "duplicate_images_within_sample": len(image_hashes) - len(set(image_hashes)),
            "field_counts": dict(fields),
            "records": records,
        }
        if len(records) != size:
            raise ValueError("Incomplete sample")
        write_json(staging / "manifest.json", manifest)
        staging.rename(output)
        return manifest
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def verify(output: Path) -> int:
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    for record in manifest["records"]:
        for field, hash_field in (("image", "image_sha256"), ("reference", "reference_sha256")):
            path = (output / record[field]).resolve()
            if not path.is_relative_to(output.resolve()):
                raise ValueError("Manifest path escapes the sample directory")
            if sha256(path) != record[hash_field]:
                raise ValueError(f"Sample checksum mismatch: {path}")
    return len(manifest["records"])
