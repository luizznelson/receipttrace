"""Offline tests for data integrity and sampling, independent of CORD downloads."""

import hashlib
import json
from pathlib import Path
from urllib.error import URLError

import pytest

from receipttrace.data import acquire, select_indices, verify


def test_sampling_is_repeatable_and_does_not_repeat_rows() -> None:
    first = select_indices(200, 20, 42)
    assert first == select_indices(200, 20, 42)
    assert first != select_indices(200, 20, 43)
    assert len(set(first)) == 20
    assert min(first) >= 0 and max(first) < 200


@pytest.mark.parametrize("size", [0, -1, 201])
def test_invalid_sample_size(size: int) -> None:
    with pytest.raises(ValueError):
        select_indices(200, size, 42)


def test_download_checks_integrity_and_reuses_verified_cache(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.write_bytes(b"receipt fixture")
    expected = hashlib.sha256(source.read_bytes()).hexdigest()
    destination = tmp_path / "cache" / "data"
    acquire(destination, source.as_uri(), expected)
    source.unlink()
    assert acquire(destination, source.as_uri(), expected).read_bytes() == b"receipt fixture"
    destination.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="Checksum"):
        acquire(destination, source.as_uri(), expected)


def test_failed_verification_never_publishes_partial_file(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.write_bytes(b"incorrect data")
    destination = tmp_path / "cache" / "data"
    with pytest.raises(ValueError, match="checksum"):
        acquire(destination, source.as_uri(), "0" * 64)
    assert not destination.exists()
    assert list(destination.parent.iterdir()) == []


def test_failed_download_cleans_temporary_file(tmp_path: Path) -> None:
    destination = tmp_path / "cache" / "data"
    with pytest.raises(URLError):
        acquire(destination, (tmp_path / "missing").as_uri())
    assert list(destination.parent.iterdir()) == []


def test_sample_verification_detects_tampering(tmp_path: Path) -> None:
    image = tmp_path / "image"
    label = tmp_path / "label"
    image.write_bytes(b"image")
    label.write_bytes(b"label")
    record = {
        "image": "image",
        "reference": "label",
        "image_sha256": hashlib.sha256(b"image").hexdigest(),
        "reference_sha256": hashlib.sha256(b"label").hexdigest(),
    }
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"records": [record]}), encoding="utf-8")
    assert verify(tmp_path) == 1
    label.write_bytes(b"changed")
    with pytest.raises(ValueError, match="checksum"):
        verify(tmp_path)


def test_manifest_paths_cannot_escape_sample(tmp_path: Path) -> None:
    manifest = {"records": [{"image": "../outside", "image_sha256": "unused"}]}
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="escapes"):
        verify(tmp_path)


def test_inspection_preserves_images_and_isolates_labels(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from io import BytesIO

    import pyarrow as pa
    import pyarrow.parquet as pq
    from PIL import Image

    from receipttrace import data

    encoded = BytesIO()
    Image.new("RGB", (4, 5), "white").save(encoded, format="PNG")
    image_bytes = encoded.getvalue()
    truth = {
        "gt_parse": {
            "menu": {"nm": "fixture", "cnt": "1", "price": "10"},
            "total": {"total_price": "10"},
        },
        "meta": {"image_id": "synthetic-fixture"},
    }
    source = tmp_path / "fixture.parquet"
    pq.write_table(
        pa.Table.from_pylist(
            [{"image": {"bytes": image_bytes}, "ground_truth": json.dumps(truth)}]
        ),
        source,
    )
    monkeypatch.setattr(data, "EXPECTED_SHA256", data.sha256(source))
    output = tmp_path / "sample"
    manifest = data.inspect(source, output, size=1)
    record = manifest["records"][0]
    assert (output / record["image"]).read_bytes() == image_bytes
    assert json.loads((output / record["reference"]).read_text()) == truth
    assert [path.suffix for path in (output / "inputs").iterdir()] == [".png"]
    assert record["dimensions"] == [4, 5]
    assert manifest["field_counts"]["items.total"] == 1
    assert data.verify(output) == 1
    with pytest.raises(FileExistsError):
        data.inspect(source, output, size=1)


def test_inspection_failure_does_not_leave_partial_sample(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    from receipttrace import data

    source = tmp_path / "fixture.parquet"
    pq.write_table(
        pa.Table.from_pylist([{"image": {"bytes": b"invalid image"}, "ground_truth": "{}"}]), source
    )
    monkeypatch.setattr(data, "EXPECTED_SHA256", data.sha256(source))
    output = tmp_path / "sample"
    with pytest.raises(ValueError):
        data.inspect(source, output, size=1)
    assert not output.exists()
    assert not list(tmp_path.glob(".inspection-*"))
