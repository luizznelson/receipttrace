"""Gemini for visitor uploads: consent, limits, fallback and secret handling. No network."""

import asyncio
import base64
import io
import json
import subprocess
import sys
from typing import Any

import pytest
from PIL import Image

pytest.importorskip("httpx")

from receipttrace.gemini import GeminiQuotaExceeded  # noqa: E402
from receipttrace.llm import Answer  # noqa: E402
from receipttrace.upload_gemini import (  # noqa: E402
    GeminiFallback,
    GeminiQuota,
    GeminiReader,
    GeminiSettings,
)
from receipttrace.upload_worker import InvalidImage, prepare_for_provider  # noqa: E402

SECRET = "synthetic-key-must-never-appear-anywhere"
ENABLED = {
    "RECEIPTTRACE_UPLOAD_GEMINI": "1",
    "RECEIPTTRACE_GEMINI_FREE_TIER": "confirmed",
}
RECEIPT = {
    "currency": "BRL",
    "items": [{"description": "Café", "quantity": "1", "unit_price": "10,00", "amount": "10,00"}],
    "items_complete": True,
    "subtotal": "10,00",
    "discount": None,
    "tax": None,
    "service": "1,00",
    "total": "11,00",
}


def png(size: tuple[int, int] = (200, 100)) -> bytes:
    output = io.BytesIO()
    Image.new("RGB", size, "white").save(output, format="PNG")
    return output.getvalue()


def prepared() -> dict[str, Any]:
    return prepare_for_provider(png(), "image/png")


class FakeProvider:
    def __init__(self, outcome: Any = None) -> None:
        self.outcome = RECEIPT if outcome is None else outcome
        self.payloads: list[dict[str, Any]] = []
        self.closed = False

    def extract(self, payload: dict[str, Any], max_output: int) -> Answer:
        self.payloads.append(payload)
        if isinstance(self.outcome, BaseException):
            raise self.outcome
        return Answer(
            json.dumps(self.outcome),
            {"status": "completed", "model": "fake-model", "usage": {"input_tokens": 3}},
        )

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def key(monkeypatch: Any) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", SECRET)


def reader(
    provider: FakeProvider | None = None, env: dict[str, str] | None = None, **quota: Any
) -> tuple[GeminiReader, FakeProvider]:
    fake = provider or FakeProvider()
    settings = GeminiSettings.from_env({**ENABLED, **(env or {})})
    instance = GeminiReader(
        settings, provider_factory=lambda config: fake, quota=GeminiQuota(settings, **quota)
    )
    return instance, fake


def read(instance: GeminiReader, client: str = "visitor") -> dict[str, Any]:
    return asyncio.run(instance.read(prepared(), "brl-grouped", client))


def reason(instance: GeminiReader, client: str = "visitor") -> str:
    with pytest.raises(GeminiFallback) as failure:
        read(instance, client)
    return failure.value.reason


def test_gemini_is_off_unless_operator_sets_both_flags_and_a_key(monkeypatch: Any) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.chdir("/")  # no .env to find
    assert not GeminiReader(GeminiSettings.from_env({})).available()
    assert not reader()[0].available()  # flags set, key missing
    monkeypatch.setenv("GEMINI_API_KEY", SECRET)
    assert reader()[0].available()
    only_requested = {"RECEIPTTRACE_UPLOAD_GEMINI": "1"}
    assert not GeminiReader(GeminiSettings.from_env(only_requested)).available()
    assert not reader(env={"RECEIPTTRACE_GEMINI_MODEL": "unlisted-model"})[0].available()


def test_settings_are_bounded_and_ignore_garbage() -> None:
    settings = GeminiSettings.from_env(
        {"RECEIPTTRACE_GEMINI_DAILY_LIMIT": "999999", "RECEIPTTRACE_GEMINI_PER_MINUTE": "x"}
    )
    assert settings.daily_limit == 500
    assert settings.per_minute_limit == 6


def test_successful_read_matches_the_ocr_contract_and_sends_only_sanitized_jpeg(
    key: None,
) -> None:
    instance, provider = reader()
    result = read(instance)
    assert result["method"] == "gemini_vision" and result["status"] == "read"
    assert result["raw"]["total"] == "11,00" and result["raw"]["service"] == "1,00"
    # Items feed the sum check but are never scored; a model-chosen currency is never trusted.
    assert result["raw"]["items"] == [] and result["raw"]["currency"] is None
    assert result["engine"]["items_read"] == 1
    assert result["items"] == [
        {"description": "Café", "quantity": "1", "unit_price": "10,00", "amount": "10,00"}
    ]
    assert result["items_check"]["status"] == "match"
    assert result["items_check"]["target"] == "subtotal"
    assert result["external_provider"] is True and result["benchmark_included"] is False
    assert result["review_status"] == "needs_human_review"
    assert result["evidence"] == {"rows": [], "fields": {}}
    assert result["validation"]["checks"]
    sent = provider.payloads[0]
    assert sent["store"] is False
    image = next(part for part in sent["input"] if part["type"] == "image")
    assert image["mime_type"] == "image/jpeg"
    assert base64.b64decode(image["data"])[:3] == b"\xff\xd8\xff"
    assert provider.closed
    assert SECRET not in json.dumps(result, default=str)


def test_empty_answer_is_explicit_and_invents_nothing(key: None) -> None:
    empty = {**RECEIPT, "subtotal": None, "service": None, "total": None, "items": []}
    result = read(reader(FakeProvider(empty))[0])
    assert result["status"] == "empty"
    assert all(result["raw"][name] is None for name in ("total", "subtotal", "tax"))


@pytest.mark.parametrize(
    ("outcome", "expected"),
    [
        (TimeoutError(), "gemini_timeout"),
        (ValueError("provider said: " + SECRET), "gemini_invalid_response"),
        (RuntimeError("socket closed " + SECRET), "gemini_error"),
        ({"total": 5}, "gemini_invalid_response"),
    ],
)
def test_failures_become_reason_codes_without_leaking_provider_text(
    key: None, outcome: Any, expected: str
) -> None:
    value = reason(reader(FakeProvider(outcome))[0])
    assert value == expected
    assert SECRET not in value


def test_http_authorization_errors_pause_gemini_for_everyone(key: None) -> None:
    class Rejected(Exception):
        response = type("Response", (), {"status_code": 403})()

    instance, provider = reader(FakeProvider(Rejected()))
    assert reason(instance) == "gemini_unavailable"
    provider.outcome = RECEIPT
    assert reason(instance, "someone-else") == "gemini_paused"
    assert len(provider.payloads) == 1  # nothing else was sent while paused


def test_provider_quota_response_pauses_and_the_pause_expires(key: None) -> None:
    now = [1000.0]
    instance, provider = reader(FakeProvider(GeminiQuotaExceeded("quota")), clock=lambda: now[0])
    assert reason(instance) == "gemini_unavailable"
    provider.outcome = RECEIPT
    assert reason(instance, "other") == "gemini_paused"
    now[0] += 3601
    assert read(instance, "other")["method"] == "gemini_vision"


def test_limits_are_per_visitor_per_day_per_minute_and_per_instance(key: None) -> None:
    now, day = [0.0], ["2026-10-30"]
    env = {
        "RECEIPTTRACE_GEMINI_CLIENT_DAILY_LIMIT": "2",
        "RECEIPTTRACE_GEMINI_DAILY_LIMIT": "4",
        "RECEIPTTRACE_GEMINI_PER_MINUTE": "3",
    }
    instance, _ = reader(env=env, clock=lambda: now[0], today=lambda: day[0])
    read(instance, "a")
    read(instance, "a")
    assert reason(instance, "a") == "gemini_client_limit"
    read(instance, "b")
    assert reason(instance, "c") == "gemini_rate_limited"
    now[0] += 61
    read(instance, "c")
    assert reason(instance, "d") == "gemini_daily_limit"
    day[0] = "2026-10-31"
    assert read(instance, "a")["method"] == "gemini_vision"


def test_concurrency_is_bounded_and_released_after_failures(key: None) -> None:
    instance, _ = reader()
    instance.quota.active = 2
    assert reason(instance) == "gemini_busy"
    instance.quota.active = 0
    instance.provider_factory = lambda config: FakeProvider(RuntimeError("x"))
    assert reason(instance) == "gemini_error"
    assert instance.quota.active == 0


def test_client_addresses_are_hashed_and_not_stored(key: None) -> None:
    instance, _ = reader()
    identifier = instance.quota.client_id("203.0.113.9")
    assert "203.0.113.9" not in identifier and len(identifier) == 16
    assert identifier == instance.quota.client_id("203.0.113.9")
    read(instance, identifier)
    assert "203.0.113.9" not in repr(instance.quota.__dict__)


def test_worker_prepares_a_metadata_free_jpeg_and_hashes_the_original() -> None:
    source = Image.new("RGB", (120, 80), "white")
    exif = Image.Exif()
    exif[270] = "synthetic-private-metadata"
    buffer = io.BytesIO()
    source.save(buffer, format="JPEG", exif=exif)
    original = buffer.getvalue()
    result = prepare_for_provider(original, "image/jpeg")
    image = base64.b64decode(result["image_base64"])
    assert b"synthetic-private-metadata" not in image
    with Image.open(io.BytesIO(image)) as decoded:
        assert decoded.format == "JPEG" and not decoded.getexif()
    assert result["bytes"] == len(original) and len(result["sha256"]) == 64
    assert result["content_type"] == "image/jpeg"
    with pytest.raises(InvalidImage):
        prepare_for_provider(b"not an image", "image/png")


def test_prepare_worker_runs_as_a_subprocess_without_provider_keys(monkeypatch: Any) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", SECRET)
    process = subprocess.run(
        [sys.executable, "-m", "receipttrace.upload_worker", "-", "image/png", "prepare"],
        input=png(),
        capture_output=True,
        check=False,
        env={"PATH": "", "PYTHONPATH": ":".join(sys.path)},
    )
    payload = json.loads(process.stdout)
    assert payload["result"]["mime_type"] == "image/jpeg"
    assert SECRET.encode() not in process.stdout + process.stderr
    bad = subprocess.run(
        [sys.executable, "-m", "receipttrace.upload_worker", "-", "image/png", "prepare"],
        input=b"junk",
        capture_output=True,
        check=False,
        env={"PATH": "", "PYTHONPATH": ":".join(sys.path)},
    )
    assert json.loads(bad.stdout) == {"error": "invalid_image"}
