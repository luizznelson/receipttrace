"""Gemini reading for visitor uploads: opt-in, free tier only, bounded, never blocks the OCR path.

The server process holds the API key. Untrusted images are decoded, oriented, stripped of
metadata and re-encoded by the sandboxed worker first; only that sanitized JPEG reaches Google.
Any refusal, quota response or failure becomes a reason code so the caller can fall back to the
local OCR and tell the visitor why.
"""

import asyncio
import base64
import hashlib
import os
import secrets
import time
from collections import deque
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from importlib.util import find_spec
from typing import Any
from uuid import uuid4

from receipttrace.credentials import api_key
from receipttrace.domain import RawReceipt, report, summarize_validation
from receipttrace.gemini import (
    GeminiFreeTierUnavailable,
    GeminiModelUnavailable,
    GeminiProvider,
    GeminiQuotaExceeded,
    GeminiSchemaTooComplex,
)
from receipttrace.llm import Answer, decode, prompt, request
from receipttrace.llm_config import LLMConfig
from receipttrace.money import NumberPolicy

RULES_VERSION = "upload-gemini-1"
CONSENT_HEADER = "x-provider-consent"
CONSENT_VALUE = "google-gemini-free"
DEFAULT_MODEL = "gemini-3.5-flash-lite"
GEMINI_TIMEOUT_SECONDS = 45.0
MAX_CLIENTS_TRACKED = 10_000
FIELDS = ("total", "subtotal", "tax", "service", "discount")


class GeminiFallback(Exception):
    """Gemini was not used or failed; the caller reads the image with local OCR instead."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def _bounded(env: Mapping[str, str], name: str, default: int, low: int, high: int) -> int:
    try:
        value = int(env.get(name, default))
    except ValueError:
        return default
    return min(max(value, low), high)


@dataclass(frozen=True)
class GeminiSettings:
    """Everything is off unless the operator sets both explicit flags and provides a key."""

    requested: bool
    free_tier_confirmed: bool
    model: str
    daily_limit: int
    client_daily_limit: int
    per_minute_limit: int
    pause_seconds: int
    max_concurrent: int = 2

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> GeminiSettings:
        env = os.environ if env is None else env
        return cls(
            requested=env.get("RECEIPTTRACE_UPLOAD_GEMINI") == "1",
            free_tier_confirmed=env.get("RECEIPTTRACE_GEMINI_FREE_TIER") == "confirmed",
            model=env.get("RECEIPTTRACE_GEMINI_MODEL", DEFAULT_MODEL),
            daily_limit=_bounded(env, "RECEIPTTRACE_GEMINI_DAILY_LIMIT", 40, 1, 500),
            client_daily_limit=_bounded(env, "RECEIPTTRACE_GEMINI_CLIENT_DAILY_LIMIT", 5, 1, 50),
            per_minute_limit=_bounded(env, "RECEIPTTRACE_GEMINI_PER_MINUTE", 6, 1, 15),
            pause_seconds=_bounded(env, "RECEIPTTRACE_GEMINI_PAUSE_SECONDS", 3600, 60, 86_400),
        )

    def config(self) -> LLMConfig:
        return LLMConfig(
            provider="gemini-free",
            model=self.model,
            thinking_level="low" if self.model == "gemini-3.8-flash" else "minimal",
            free_tier_confirmed=self.free_tier_confirmed,
            max_requests=1,
            max_output_tokens=4096,
            max_input_tokens=20_000,
            max_budget_usd="0",
            input_usd_per_million="0",
            output_usd_per_million="0",
            pricing_as_of=datetime.now(UTC).date().isoformat(),
        )


class GeminiQuota:
    """Conservative in-memory limits. They reset when the process restarts, so they are a
    politeness guard, not a billing control: Google's own free-tier quota is the hard limit,
    and a quota or authorization response pauses Gemini for the whole instance."""

    def __init__(
        self,
        settings: GeminiSettings,
        *,
        clock: Callable[[], float] = time.monotonic,
        today: Callable[[], str] = lambda: datetime.now(UTC).date().isoformat(),
    ) -> None:
        self.settings = settings
        self.clock = clock
        self.today = today
        self.salt = secrets.token_bytes(16)
        self.recent: deque[float] = deque()
        self.day = today()
        self.used_today = 0
        self.clients: dict[str, int] = {}
        self.paused_until = 0.0
        self.active = 0

    def client_id(self, address: str) -> str:
        # Salted hash: the address is never stored, and the salt dies with the process.
        return hashlib.sha256(self.salt + address.encode("utf-8", "replace")).hexdigest()[:16]

    def reserve(self, client: str) -> None:
        now = self.clock()
        if self.today() != self.day:
            self.day, self.used_today, self.clients = self.today(), 0, {}
        if now < self.paused_until:
            raise GeminiFallback("gemini_paused")
        if self.used_today >= self.settings.daily_limit:
            raise GeminiFallback("gemini_daily_limit")
        known = client in self.clients
        if (not known and len(self.clients) >= MAX_CLIENTS_TRACKED) or (
            self.clients.get(client, 0) >= self.settings.client_daily_limit
        ):
            raise GeminiFallback("gemini_client_limit")
        while self.recent and now - self.recent[0] >= 60:
            self.recent.popleft()
        if len(self.recent) >= self.settings.per_minute_limit:
            raise GeminiFallback("gemini_rate_limited")
        if self.active >= self.settings.max_concurrent:
            raise GeminiFallback("gemini_busy")
        self.recent.append(now)
        self.used_today += 1
        self.clients[client] = self.clients.get(client, 0) + 1
        self.active += 1

    def release(self) -> None:
        self.active = max(0, self.active - 1)

    def pause(self) -> None:
        self.paused_until = self.clock() + self.settings.pause_seconds


class GeminiReader:
    def __init__(
        self,
        settings: GeminiSettings | None = None,
        *,
        provider_factory: Callable[[LLMConfig], Any] | None = None,
        quota: GeminiQuota | None = None,
    ) -> None:
        self.settings = settings or GeminiSettings.from_env()
        self.quota = quota or GeminiQuota(self.settings)
        self.provider_factory = provider_factory or (
            lambda config: GeminiProvider(config, timeout=GEMINI_TIMEOUT_SECONDS)
        )

    def available(self) -> bool:
        settings = self.settings
        if not (settings.requested and settings.free_tier_confirmed):
            return False
        try:
            settings.config()
            api_key("GEMINI_API_KEY")
        except ValueError:
            return False
        return find_spec("httpx") is not None

    def describe(self) -> dict[str, Any]:
        return {
            "available": self.available(),
            "model": self.settings.model,
            "tier": "free",
            "daily_limit": self.settings.daily_limit,
            "client_daily_limit": self.settings.client_daily_limit,
            "consent": CONSENT_VALUE,
        }

    def _call(self, prepared: dict[str, Any], document_id: str) -> tuple[RawReceipt, Answer]:
        config = self.settings.config()
        image = base64.b64decode(prepared["image_base64"], validate=True)
        payload = request(image, config, mime_type=prepared["mime_type"])
        provider = self.provider_factory(config)
        try:
            answer = provider.extract(payload, config.max_output_tokens)
        finally:
            provider.close()
        return decode(answer, document_id), answer

    async def read(
        self, prepared: dict[str, Any], policy: NumberPolicy, client: str
    ) -> dict[str, Any]:
        if not self.available():
            raise GeminiFallback("gemini_unavailable")
        self.quota.reserve(client)
        started = time.perf_counter()
        document_id = "upload-" + uuid4().hex
        try:
            raw, answer = await asyncio.wait_for(
                asyncio.to_thread(self._call, prepared, document_id),
                timeout=GEMINI_TIMEOUT_SECONDS + 5,
            )
        except TimeoutError:
            raise GeminiFallback("gemini_timeout") from None
        except (
            GeminiQuotaExceeded,
            GeminiFreeTierUnavailable,
            GeminiModelUnavailable,
            GeminiSchemaTooComplex,
        ):
            self.quota.pause()
            raise GeminiFallback("gemini_unavailable") from None
        except ValueError:
            # Incomplete, refused or contract-breaking answers; never echo provider content.
            raise GeminiFallback("gemini_invalid_response") from None
        except Exception as error:
            # httpx timeouts, network failures and HTTP errors. Message bodies stay out of logs.
            status = getattr(getattr(error, "response", None), "status_code", None)
            if status in {401, 403}:
                self.quota.pause()
                raise GeminiFallback("gemini_unavailable") from None
            if "Timeout" in type(error).__name__:
                raise GeminiFallback("gemini_timeout") from None
            raise GeminiFallback("gemini_error") from None
        finally:
            self.quota.release()
        return self.result(raw, answer, prepared, policy, document_id, started)

    def result(
        self,
        raw: RawReceipt,
        answer: Answer,
        prepared: dict[str, Any],
        policy: NumberPolicy,
        document_id: str,
        started: float,
    ) -> dict[str, Any]:
        # Same contract as the OCR result: five fields only; items are not evaluated live.
        ignored = len(raw.items)
        fields = raw.model_copy(update={"items": [], "currency": None, "items_complete": False})
        validation = report(fields, policy, Decimal(0))
        found = any(getattr(fields, name) is not None for name in FIELDS)
        usage = answer.response.get("usage")
        return {
            "schema_version": 1,
            "document_id": document_id,
            "created_at_utc": datetime.now(UTC).isoformat(),
            "source": {
                "sha256": prepared["sha256"],
                "bytes": prepared["bytes"],
                "content_type": prepared["content_type"],
                **prepared["dimensions"],
            },
            "method": "gemini_vision",
            "rules_version": RULES_VERSION,
            "engine": {
                "provider": "gemini-free",
                "requested_model": self.settings.model,
                "model": answer.response.get("model"),
                "api": "interactions-v1beta",
                "thinking_level": self.settings.config().thinking_level,
                "prompt_sha256": hashlib.sha256(prompt().encode()).hexdigest(),
                "usage": usage if isinstance(usage, dict) else None,
                "items_ignored": ignored,
                "sent_to_provider": "sanitized_jpeg_without_metadata",
            },
            "numeric_policy": policy,
            "status": "read" if found else "empty",
            "raw": fields.model_dump(),
            "validation": validation,
            "arithmetic": summarize_validation(validation),
            "lines": [],
            "evidence": {"rows": [], "fields": {}},
            "seconds": round(time.perf_counter() - started, 3),
            "retention": "request_memory_only",
            "external_provider": True,
            "benchmark_included": False,
            "review_status": "needs_human_review",
        }
