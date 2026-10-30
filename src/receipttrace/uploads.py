"""Bounded live reading of one temporary image: local OCR, or Gemini when the visitor opts in.

Nothing is persisted. The OCR worker never receives provider keys; the Gemini call happens in the
server process only after the worker has sanitized the image, and any Gemini problem falls back
to the local OCR with an explicit reason instead of failing the visitor's test.
"""

import asyncio
import json
import os
import sys
import time
from collections import deque
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from importlib.util import find_spec
from typing import Any

from receipttrace.money import NumberPolicy
from receipttrace.upload_gemini import GeminiFallback, GeminiReader
from receipttrace.upload_worker import MAX_PIXELS, MAX_UPLOAD_BYTES

UPLOAD_TIMEOUT_SECONDS = 60.0
UPLOAD_POLICIES = ("brl-grouped", "usd-grouped", "idr-grouped")
OCR_OUTPUT_LIMIT = 4 * 1024 * 1024
PREPARED_OUTPUT_LIMIT = 16 * 1024 * 1024
USER_ERRORS = {"invalid_image", "image_dimensions", "image_too_complex"}


class UploadRejected(Exception):
    def __init__(self, code: str, status: int) -> None:
        self.code, self.status = code, status
        super().__init__(code)


class UploadService:
    def __init__(self, enabled: bool, gemini: GeminiReader | None = None) -> None:
        self.enabled = enabled
        self.gemini = gemini if gemini is not None else GeminiReader()
        self.busy = False
        self.recent: deque[float] = deque(maxlen=10)

    @staticmethod
    def available() -> bool:
        return find_spec("rapidocr") is not None and find_spec("onnxruntime") is not None

    def capabilities(self) -> dict[str, Any]:
        ocr = self.enabled and self.available()
        gemini = {**self.gemini.describe()}
        gemini["available"] = self.enabled and bool(gemini["available"])
        return {
            "enabled": ocr or gemini["available"],
            "max_bytes": MAX_UPLOAD_BYTES,
            "max_pixels": MAX_PIXELS,
            "formats": ["image/png", "image/jpeg"],
            "policies": UPLOAD_POLICIES,
            "retention": "request_memory_only",
            "timeout_seconds": UPLOAD_TIMEOUT_SECONDS,
            "max_concurrent": 1,
            "max_requests_per_minute": 10,
            "engines": {"ocr": {"available": ocr}, "gemini": gemini},
            "default_engine": "gemini" if gemini["available"] else "ocr",
            "external_provider": gemini["available"],
        }

    @asynccontextmanager
    async def _slot(self, *, count_rate: bool = True) -> AsyncIterator[None]:
        if self.busy:
            raise UploadRejected("ocr_busy", 429)
        now = time.monotonic()
        while self.recent and now - self.recent[0] >= 60:
            self.recent.popleft()
        if count_rate:
            if len(self.recent) >= 10:
                raise UploadRejected("upload_rate_limited", 429)
            self.recent.append(now)
        self.busy = True
        try:
            yield
        finally:
            self.busy = False

    @staticmethod
    async def _worker(arguments: list[str], body: bytes, output_limit: int) -> dict[str, Any]:
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
                *arguments,
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
            if process.returncode != 0 or len(output) > output_limit:
                raise UploadRejected("ocr_failed", 503)
            result = json.loads(output)
            if "error" in result:
                code = result["error"]
                raise UploadRejected(code, 422 if code in USER_ERRORS else 503)
            return dict(result["result"])
        finally:
            if process is not None and process.returncode is None:
                with suppress(ProcessLookupError):
                    process.kill()
                await process.wait()

    async def extract(
        self, body: bytes, policy: NumberPolicy, content_type: str, *, count_rate: bool = True
    ) -> dict[str, Any]:
        """Local OCR only. Never contacts a provider."""
        if not self.enabled or not self.available():
            raise UploadRejected("ocr_unavailable", 503)
        async with self._slot(count_rate=count_rate):
            return await self._worker([policy, content_type], body, OCR_OUTPUT_LIMIT)

    async def prepare(self, body: bytes, content_type: str) -> dict[str, Any]:
        async with self._slot():
            return await self._worker(["-", content_type, "prepare"], body, PREPARED_OUTPUT_LIMIT)

    async def read(
        self,
        body: bytes,
        policy: NumberPolicy,
        content_type: str,
        *,
        engine: str = "ocr",
        consent: bool = False,
        client: str = "unknown",
    ) -> dict[str, Any]:
        """Dispatch by the visitor's choice. Gemini needs explicit consent on every request."""
        if engine == "ocr":
            return await self.extract(body, policy, content_type)
        if engine != "gemini":
            raise UploadRejected("invalid_engine", 400)
        if not consent:
            raise UploadRejected("consent_required", 400)
        if not self.enabled:
            raise UploadRejected("ocr_unavailable", 503)
        reason: str
        if not self.gemini.available():
            reason = "gemini_unavailable"
        else:
            prepared = await self.prepare(body, content_type)
            try:
                return await self.gemini.read(prepared, policy, self.gemini.quota.client_id(client))
            except GeminiFallback as fallback:
                reason = fallback.reason
        # The visitor still gets a reading, and is told why it came from the local OCR.
        result = await self.extract(body, policy, content_type, count_rate=False)
        result["fallback"] = {"from": "gemini_vision", "reason": reason}
        return result
