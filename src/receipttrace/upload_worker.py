"""One-shot OCR subprocess. Image and extracted text stay in process memory."""

import base64
import hashlib
import io
import json
import sys
import time
import warnings
from contextlib import redirect_stdout
from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Literal, cast
from uuid import uuid4

from PIL import Image, ImageOps

from receipttrace.cli_serialization import decimal_json
from receipttrace.domain import report, summarize_validation
from receipttrace.money import NumberPolicy
from receipttrace.upload_rules import RULES_VERSION, parse_upload

MAX_UPLOAD_BYTES = 8 * 1024 * 1024
MAX_PIXELS = 12_000_000
MAX_SIDE = 12_000
OCR_SIDE = 2400


class InvalidImage(ValueError):
    """Unsupported, damaged or resource-intensive image."""


def prepare_image(
    data: bytes,
    content_type: str,
    *,
    output_format: Literal["PNG", "JPEG"] = "PNG",
) -> tuple[bytes, dict[str, Any]]:
    """Validate, orient, strip metadata and re-encode. PNG feeds OCR; JPEG feeds a provider."""
    if not data or len(data) > MAX_UPLOAD_BYTES:
        raise InvalidImage("invalid_image")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as source:
                expected = {"image/png": "PNG", "image/jpeg": "JPEG"}.get(content_type)
                if (
                    source.format != expected
                    or expected is None
                    or getattr(source, "n_frames", 1) != 1
                ):
                    raise InvalidImage("invalid_image")
                width, height = source.size
                if (
                    min(width, height) < 32
                    or max(width, height) > MAX_SIDE
                    or width * height > MAX_PIXELS
                ):
                    raise InvalidImage("image_dimensions")
                source.verify()
            with Image.open(io.BytesIO(data)) as source:
                image = ImageOps.exif_transpose(source).convert("RGB")
                image.thumbnail((OCR_SIDE, OCR_SIDE))
                image.info.clear()
                output = io.BytesIO()
                if output_format == "JPEG":
                    # Smaller payload for a remote model; quality stays high for small print.
                    image.save(output, format="JPEG", quality=92, optimize=True)
                else:
                    image.save(output, format="PNG")
                return output.getvalue(), {
                    "width": width,
                    "height": height,
                    "processed_width": image.width,
                    "processed_height": image.height,
                    "resized": (image.width, image.height) != (width, height),
                }
    except (
        OSError,
        SyntaxError,
        ValueError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as error:
        if isinstance(error, InvalidImage):
            raise
        raise InvalidImage("invalid_image") from None


def extract(data: bytes, policy: NumberPolicy, content_type: str) -> dict[str, Any]:
    started = time.perf_counter()
    pixels, dimensions = prepare_image(data, content_type)
    from receipttrace.ocr import Engine

    engine = Engine()
    lines = engine.read_image(pixels)
    if len(lines) > 1500 or any(len(line.text) > 1000 for line in lines):
        raise InvalidImage("image_too_complex")
    document_id = "upload-" + uuid4().hex
    raw, evidence = parse_upload(lines, document_id, policy)
    validation = report(raw, policy, Decimal(0))
    return {
        "schema_version": 1,
        "document_id": document_id,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "source": {
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
            "content_type": content_type,
            **dimensions,
        },
        "method": "local_ocr",
        "rules_version": RULES_VERSION,
        "engine": engine.metadata,
        "numeric_policy": policy,
        "status": "read" if lines else "empty",
        "raw": raw.model_dump(),
        "validation": validation,
        "arithmetic": summarize_validation(validation),
        "lines": [asdict(line) for line in lines],
        "evidence": evidence,
        "seconds": round(time.perf_counter() - started, 3),
        "retention": "request_memory_only",
        "benchmark_included": False,
        "review_status": "needs_human_review",
    }


def prepare_for_provider(data: bytes, content_type: str) -> dict[str, Any]:
    """Sanitized JPEG for a remote model. Runs in the worker, never in the server process."""
    image, dimensions = prepare_image(data, content_type, output_format="JPEG")
    return {
        "content_type": content_type,
        "mime_type": "image/jpeg",
        "image_base64": base64.b64encode(image).decode("ascii"),
        "dimensions": dimensions,
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
    }


def main() -> None:
    payload: dict[str, Any]
    try:
        data = sys.stdin.buffer.read(MAX_UPLOAD_BYTES + 1)
        # Dependency output must never corrupt the JSON response or leak to the server log.
        with redirect_stdout(sys.stderr):
            if len(sys.argv) > 3 and sys.argv[3] == "prepare":
                result = prepare_for_provider(data, sys.argv[2])
            else:
                result = extract(data, cast(NumberPolicy, sys.argv[1]), sys.argv[2])
        payload = {"result": result}
    except InvalidImage as error:
        payload = {"error": str(error)}
    except ImportError, FileNotFoundError:
        payload = {"error": "ocr_unavailable"}
    except Exception:
        payload = {"error": "ocr_failed"}
    sys.stdout.write(json.dumps(payload, ensure_ascii=True, default=decimal_json))


if __name__ == "__main__":
    main()
