"""Bounded live OCR service; no credentials, shared results or image persistence."""

import asyncio
import json
import os
import sys
import time
from collections import deque
from contextlib import suppress
from importlib.util import find_spec
from typing import Any

from receipttrace.money import NumberPolicy
from receipttrace.upload_worker import MAX_PIXELS, MAX_UPLOAD_BYTES

UPLOAD_TIMEOUT_SECONDS = 60.0
UPLOAD_POLICIES = ("brl-grouped", "usd-grouped", "idr-grouped")


class UploadRejected(Exception):
    def __init__(self, code: str, status: int) -> None:
        self.code, self.status = code, status
        super().__init__(code)


class UploadService:
    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled
        self.busy = False
        self.recent: deque[float] = deque(maxlen=10)

    @staticmethod
    def available() -> bool:
        return find_spec("rapidocr") is not None and find_spec("onnxruntime") is not None

    def capabilities(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled and self.available(),
            "max_bytes": MAX_UPLOAD_BYTES,
            "max_pixels": MAX_PIXELS,
            "formats": ["image/png", "image/jpeg"],
            "policies": UPLOAD_POLICIES,
            "retention": "request_memory_only",
            "timeout_seconds": UPLOAD_TIMEOUT_SECONDS,
            "max_concurrent": 1,
            "max_requests_per_minute": 10,
            "external_provider": False,
        }

    async def extract(self, body: bytes, policy: NumberPolicy, content_type: str) -> dict[str, Any]:
        if not self.enabled or not self.available():
            raise UploadRejected("ocr_unavailable", 503)
        if self.busy:
            raise UploadRejected("ocr_busy", 429)
        now = time.monotonic()
        while self.recent and now - self.recent[0] >= 60:
            self.recent.popleft()
        if len(self.recent) >= 10:
            raise UploadRejected("upload_rate_limited", 429)
        self.recent.append(now)
        self.busy = True
        process: asyncio.subprocess.Process | None = None
        try:
            # Explicit allowlist: provider keys and application secrets are not inherited.
            environment = {
                key: value
                for key, value in os.environ.items()
                if key.upper()
                in {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "USERPROFILE", "HOME"}
            }
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-m",
                "receipttrace.upload_worker",
                policy,
                content_type,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
                env=environment,
            )
            try:
                output, _ = await asyncio.wait_for(
                    process.communicate(body), timeout=UPLOAD_TIMEOUT_SECONDS
                )
            except TimeoutError:
                raise UploadRejected("ocr_timeout", 504) from None
            if process.returncode != 0 or len(output) > 4 * 1024 * 1024:
                raise UploadRejected("ocr_failed", 503)
            result = json.loads(output)
            if "error" in result:
                code = result["error"]
                status = (
                    422
                    if code in {"invalid_image", "image_dimensions", "image_too_complex"}
                    else 503
                )
                raise UploadRejected(code, status)
            return dict(result["result"])
        finally:
            if process is not None and process.returncode is None:
                with suppress(ProcessLookupError):
                    process.kill()
                await process.wait()
            self.busy = False
