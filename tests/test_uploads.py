"""Temporary receipt uploads: parsing, privacy boundaries and process cleanup."""

import asyncio
import hashlib
import io
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from PIL import Image

from receipttrace.money import money
from receipttrace.ocr_rules import Line
from receipttrace.upload_rules import parse_upload
from receipttrace.upload_worker import InvalidImage, extract, prepare_image


def image_bytes(format: str = "PNG", size: tuple[int, int] = (100, 100)) -> bytes:
    output = io.BytesIO()
    Image.new("RGB", size, "white").save(output, format=format)
    return output.getvalue()


def line(text: str, y: int) -> Line:
    return Line(text, 0.9, ((0.0, float(y)), (200.0, float(y)), (200.0, y + 10.0), (0.0, y + 10.0)))


@pytest.mark.parametrize(
    ("text", "policy", "expected"),
    [
        ("R$ 1.234,56", "brl-grouped", "1234.56"),
        ("1.234", "brl-grouped", "1234"),
        ("12,50", "brl-grouped", "12.50"),
        ("$ 1,234.56", "usd-grouped", "1234.56"),
        ("12.50", "usd-grouped", "12.50"),
        ("61,799", "idr-grouped", "61799"),
    ],
)
def test_explicit_numeric_conventions(text: str, policy: Any, expected: str) -> None:
    assert money(text, policy).value == Decimal(expected)


@pytest.mark.parametrize("value", ["1,234.56", "1.23,45", "1..234,56", "-1,00", "9" * 65])
def test_brazilian_policy_rejects_incompatible_or_invalid_amounts(value: str) -> None:
    assert money(value, "brl-grouped").status == "invalid"


def test_portuguese_totals_do_not_confuse_payment_or_change() -> None:
    lines = [
        line(text, i * 20)
        for i, text in enumerate(
            [
                "SUBTOTAL R$ 100,00",
                "DESCONTO 5,00",
                "SERVIÇO 10% 9,50",
                "TOTAL A PAGAR R$ 104,50",
                "PAGAMENTO DINHEIRO 120,00",
                "TROCO 15,50",
            ]
        )
    ]
    raw, evidence = parse_upload(lines, "test", "brl-grouped")
    assert raw.total == "R$ 104,50"
    assert raw.subtotal == "R$ 100,00"
    assert raw.discount == "5,00"
    assert raw.service == "9,50"
    assert raw.tax is None
    assert raw.items == [] and not raw.items_complete
    assert evidence["fields"]["total"]["candidates"][0]["row"] == 3


def test_conflicting_totals_remain_blank_with_evidence() -> None:
    raw, evidence = parse_upload(
        [line("TOTAL 10,00", 0), line("TOTAL 20,00", 20)], "test", "brl-grouped"
    )
    assert raw.total is None
    assert evidence["fields"]["total"]["ambiguous"] is True
    assert len(evidence["fields"]["total"]["candidates"]) == 2


def test_explicit_grand_total_has_priority_without_using_largest_amount() -> None:
    raw, _ = parse_upload(
        [line("TOTAL 120.00", 0), line("GRAND TOTAL 104.50", 20)], "test", "usd-grouped"
    )
    assert raw.total == "104.50"


@pytest.mark.parametrize(("format", "content_type"), [("PNG", "image/png"), ("JPEG", "image/jpeg")])
def test_image_is_reencoded_in_memory_without_metadata(format: str, content_type: str) -> None:
    data = image_bytes(format)
    encoded, info = prepare_image(data, content_type)
    assert info["width"] == 100 and not info["resized"]
    with Image.open(io.BytesIO(encoded)) as image:
        assert image.format == "PNG"
        assert image.mode == "RGB"
        assert not image.getexif()


@pytest.mark.parametrize(
    ("data", "content_type"),
    [
        (b"", "image/png"),
        (b"<svg>not a PNG</svg>", "image/png"),
        (image_bytes("JPEG"), "image/png"),
        (image_bytes(), "text/plain"),
        (image_bytes()[:40], "image/png"),
    ],
)
def test_invalid_files_do_not_reach_ocr(data: bytes, content_type: str) -> None:
    with pytest.raises(InvalidImage):
        prepare_image(data, content_type)


def test_dimensions_checked_before_pixel_processing_and_large_image_resized() -> None:
    with pytest.raises(InvalidImage, match="image_dimensions"):
        prepare_image(image_bytes(size=(4000, 4000)), "image/png")
    with pytest.raises(InvalidImage, match="image_dimensions"):
        prepare_image(image_bytes(size=(20, 100)), "image/png")
    _, info = prepare_image(image_bytes(size=(3000, 100)), "image/png")
    assert info["resized"] and info["processed_width"] == 2400


def test_live_result_preserves_source_and_never_claims_benchmark_accuracy(monkeypatch: Any) -> None:
    class FakeEngine:
        metadata = {"engine": "synthetic-test"}

        def read_image(self, data: bytes) -> list[Line]:
            return [line("TOTAL 10,50", 0)]

    monkeypatch.setattr("receipttrace.ocr.Engine", FakeEngine)
    data = image_bytes()
    result = extract(data, "brl-grouped", "image/png")
    assert result["source"]["sha256"] == hashlib.sha256(data).hexdigest()
    assert result["raw"]["total"] == "10,50"
    assert result["retention"] == "request_memory_only"
    assert result["benchmark_included"] is False
    assert result["review_status"] == "needs_human_review"
    assert result["arithmetic"]["status"] == "not_checked"


def test_empty_ocr_is_explicit_and_does_not_invent_values(monkeypatch: Any) -> None:
    class EmptyEngine:
        metadata: dict[str, Any] = {}

        def read_image(self, data: bytes) -> list[Line]:
            return []

    monkeypatch.setattr("receipttrace.ocr.Engine", EmptyEngine)
    result = extract(image_bytes(), "brl-grouped", "image/png")
    assert result["status"] == "empty"
    assert result["raw"]["total"] is None


def test_process_timeout_kills_worker_and_releases_slot(monkeypatch: Any) -> None:
    pytest.importorskip("fastapi")
    from receipttrace import uploads

    class Process:
        returncode = None
        killed = False

        async def communicate(self, body: bytes) -> Any:
            await asyncio.sleep(1)

        def kill(self) -> None:
            self.killed = True

        async def wait(self) -> None:
            self.returncode = -1

    process = Process()

    async def spawn(*args: Any, **kwargs: Any) -> Any:
        assert "GEMINI_API_KEY" not in kwargs["env"]
        assert "OPENAI_API_KEY" not in kwargs["env"]
        return process

    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-secret-never-pass-to-ocr")
    monkeypatch.setattr(uploads.asyncio, "create_subprocess_exec", spawn)
    monkeypatch.setattr(uploads, "UPLOAD_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(uploads.UploadService, "available", staticmethod(lambda: True))
    service = uploads.UploadService(True)
    with pytest.raises(uploads.UploadRejected) as failure:
        asyncio.run(service.extract(b"test", "brl-grouped", "image/png"))
    assert failure.value.code == "ocr_timeout"
    assert process.killed and not service.busy


def test_concurrency_and_shared_rate_limit_are_bounded(monkeypatch: Any) -> None:
    pytest.importorskip("fastapi")
    import time

    from receipttrace.uploads import UploadRejected, UploadService

    monkeypatch.setattr(UploadService, "available", staticmethod(lambda: True))
    service = UploadService(True)
    service.busy = True
    with pytest.raises(UploadRejected) as failure:
        asyncio.run(service.extract(b"", "brl-grouped", "image/png"))
    assert failure.value.code == "ocr_busy"
    service.busy = False
    service.recent.extend([time.monotonic()] * 10)
    with pytest.raises(UploadRejected) as failure:
        asyncio.run(service.extract(b"", "brl-grouped", "image/png"))
    assert failure.value.code == "upload_rate_limited"
    assert len(service.recent) == 10


def test_public_upload_is_ephemeral_and_does_not_expose_local_reviews(
    tmp_path: Path, monkeypatch: Any
) -> None:
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx2")
    from fastapi.testclient import TestClient

    from receipttrace.uploads import UploadService
    from receipttrace.web import create_app

    seen: list[bytes] = []

    async def extract(self: Any, body: bytes, policy: Any, content_type: str) -> Any:
        seen.append(body)
        assert policy == "brl-grouped" and content_type == "image/png"
        return {"status": "synthetic-test"}

    monkeypatch.setattr(UploadService, "extract", extract)
    database = tmp_path / "reviews.sqlite3"
    client = TestClient(create_app(read_only=True, allow_uploads=True, database=database))
    data = image_bytes()
    assert (
        client.post("/api/uploads", content=data, headers={"content-type": "image/png"}).status_code
        == 200
    )
    assert seen == [data]
    assert client.post("/api/reviews", json={}).status_code == 403
    assert client.get("/api/reviews/00000000-0000-0000-0000-000000000000").status_code == 403
    response = client.post(
        "/api/uploads/validate",
        json={"raw": {"document_id": "test", "total": "1.234,56"}, "policy": "brl-grouped"},
    )
    assert response.status_code == 200
    assert response.json()["normalized"]["total"]["value"] == "1234.56"
    assert not database.exists()


@pytest.mark.parametrize(
    ("headers", "expected"),
    [
        ({"origin": "https://foreign.example"}, 403),
        ({"content-type": "application/pdf"}, 415),
        ({"content-length": str(8 * 1024 * 1024 + 1)}, 413),
    ],
)
def test_upload_request_limits_apply_in_read_only_mode(headers: Any, expected: int) -> None:
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx2")
    from fastapi.testclient import TestClient

    from receipttrace.web import create_app

    client = TestClient(create_app(allow_uploads=True))
    response = client.post(
        "/api/uploads", content=b"test", headers={"content-type": "image/png", **headers}
    )
    assert response.status_code == expected
    assert response.headers["cache-control"] == "no-store"


def test_upload_is_disabled_by_default() -> None:
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx2")
    from fastapi.testclient import TestClient

    from receipttrace.web import create_app

    client = TestClient(create_app())
    assert client.get("/api/uploads/capabilities").json()["enabled"] is False
    assert (
        client.post(
            "/api/uploads", content=b"test", headers={"content-type": "image/png"}
        ).status_code
        == 403
    )


def test_image_metadata_is_not_forwarded_to_ocr() -> None:
    source = Image.new("RGB", (100, 100), "white")
    exif = Image.Exif()
    exif[270] = "synthetic-private-metadata"
    buffer = io.BytesIO()
    source.save(buffer, format="JPEG", exif=exif)
    prepared, _ = prepare_image(buffer.getvalue(), "image/jpeg")
    assert b"synthetic-private-metadata" not in prepared
    with Image.open(io.BytesIO(prepared)) as normalized:
        assert not normalized.getexif()


def test_validation_never_assumes_missing_components_are_zero() -> None:
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx2")
    from fastapi.testclient import TestClient

    from receipttrace.web import create_app

    client = TestClient(create_app(allow_uploads=True))
    raw = {"document_id": "synthetic", "subtotal": "10,00", "total": "10,00"}
    body = {"raw": raw, "policy": "brl-grouped"}
    response = client.post("/api/uploads/validate", json=body)
    assert response.status_code == 200
    assert all(check["status"] == "skipped" for check in response.json()["checks"])
    raw.update(discount="0", tax="0", service="0")
    response = client.post("/api/uploads/validate", json=body)
    assert (
        next(check for check in response.json()["checks"] if check["code"] == "receipt_total")[
            "status"
        ]
        == "pass"
    )
    raw["total"] = "11,00"
    response = client.post("/api/uploads/validate", json=body)
    assert (
        next(check for check in response.json()["checks"] if check["code"] == "receipt_total")[
            "status"
        ]
        == "mismatch"
    )
    raw["total"] = "malformed"
    response = client.post("/api/uploads/validate", json=body)
    assert response.json()["normalized"]["total"]["status"] == "invalid"


def test_validation_bounds_user_fields_and_rejects_item_injection() -> None:
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx2")
    from fastapi.testclient import TestClient

    from receipttrace.web import create_app

    client = TestClient(create_app(allow_uploads=True))
    for extra in [
        {"total": "1" * 65},
        {"items": [{"description": "not supported"}]},
        {"items_complete": True},
    ]:
        response = client.post(
            "/api/uploads/validate",
            json={"raw": {"document_id": "synthetic", **extra}, "policy": "brl-grouped"},
        )
        assert response.status_code == 422


def test_saved_example_can_be_checked_without_enabling_ocr_or_storage(tmp_path: Path) -> None:
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx2")
    from fastapi.testclient import TestClient

    from receipttrace.web import create_app

    database = tmp_path / "private.sqlite3"
    client = TestClient(create_app(read_only=True, allow_uploads=False, database=database))
    detail = client.get("/api/examples/cord-train-shard0-row0006?method=ocr").json()
    raw = {"document_id": detail["id"], "total": "61,799"}
    response = client.post("/api/uploads/validate", json={"raw": raw, "policy": "idr-grouped"})
    assert response.status_code == 200
    assert response.json()["normalized"]["total"]["value"] == "61799"
    assert client.post("/api/reviews", json={}).status_code == 403
    assert (
        client.post(
            "/api/uploads", content=b"image", headers={"content-type": "image/png"}
        ).status_code
        == 403
    )
    assert not database.exists()
