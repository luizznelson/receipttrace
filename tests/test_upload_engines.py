"""Engine choice for uploads: default stays local, Gemini needs consent and falls back to OCR."""

import asyncio
from typing import Any

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx2")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from receipttrace.upload_gemini import (  # noqa: E402
    CONSENT_HEADER,
    CONSENT_VALUE,
    GeminiFallback,
    GeminiReader,
    GeminiSettings,
)
from receipttrace.uploads import UploadRejected, UploadService  # noqa: E402
from receipttrace.web import client_address, create_app  # noqa: E402

PNG = {"content-type": "image/png"}


class StubReader(GeminiReader):
    """A reader whose availability and outcome are scripted; it never reaches a provider."""

    def __init__(self, *, available: bool = True, outcome: Any = None) -> None:
        super().__init__(GeminiSettings.from_env({}))
        self._available, self.outcome, self.calls = available, outcome, 0

    def available(self) -> bool:
        return self._available

    async def read(self, prepared: Any, policy: Any, client: str) -> dict[str, Any]:
        self.calls += 1
        if isinstance(self.outcome, GeminiFallback):
            raise self.outcome
        return self.outcome or {"method": "gemini_vision", "client": client}


def service(reader: StubReader, monkeypatch: Any) -> tuple[UploadService, dict[str, Any]]:
    seen: dict[str, Any] = {"prepared": 0, "ocr": []}

    async def prepare(self: Any, body: bytes, content_type: str) -> dict[str, Any]:
        seen["prepared"] += 1
        return {"image_base64": "AA==", "mime_type": "image/jpeg"}

    async def extract(self: Any, body: bytes, policy: Any, content_type: str, **kw: Any) -> Any:
        seen["ocr"].append(kw)
        return {"method": "local_ocr"}

    monkeypatch.setattr(UploadService, "prepare", prepare)
    monkeypatch.setattr(UploadService, "extract", extract)
    return UploadService(True, reader), seen


def run(instance: UploadService, **options: Any) -> Any:
    return asyncio.run(instance.read(b"img", "brl-grouped", "image/png", **options))


def test_default_engine_is_local_and_never_touches_gemini(monkeypatch: Any) -> None:
    reader = StubReader()
    instance, seen = service(reader, monkeypatch)
    assert run(instance)["method"] == "local_ocr"
    assert reader.calls == 0 and seen["prepared"] == 0


def test_gemini_requires_consent_on_every_request_and_sends_nothing_without_it(
    monkeypatch: Any,
) -> None:
    reader = StubReader()
    instance, seen = service(reader, monkeypatch)
    with pytest.raises(UploadRejected) as failure:
        run(instance, engine="gemini", consent=False)
    assert (failure.value.code, failure.value.status) == ("consent_required", 400)
    with pytest.raises(UploadRejected) as unknown:
        run(instance, engine="other", consent=True)
    assert unknown.value.code == "invalid_engine"
    assert reader.calls == 0 and seen["prepared"] == 0 and seen["ocr"] == []


def test_gemini_result_is_returned_when_consent_is_given(monkeypatch: Any) -> None:
    reader = StubReader()
    instance, seen = service(reader, monkeypatch)
    result = run(instance, engine="gemini", consent=True, client="visitor")
    assert result["method"] == "gemini_vision" and "fallback" not in result
    assert seen["ocr"] == [] and reader.calls == 1
    assert result["client"] != "visitor"  # the reader receives a hashed identifier


@pytest.mark.parametrize("reason", ["gemini_daily_limit", "gemini_timeout", "gemini_paused"])
def test_any_gemini_problem_falls_back_to_ocr_and_says_why(monkeypatch: Any, reason: str) -> None:
    instance, seen = service(StubReader(outcome=GeminiFallback(reason)), monkeypatch)
    result = run(instance, engine="gemini", consent=True)
    assert result["method"] == "local_ocr"
    assert result["fallback"] == {"from": "gemini_vision", "reason": reason}
    assert seen["ocr"] == [{"count_rate": False}]  # one visitor action, one rate-limit slot


def test_unavailable_gemini_skips_preparation_and_uses_ocr(monkeypatch: Any) -> None:
    instance, seen = service(StubReader(available=False), monkeypatch)
    result = run(instance, engine="gemini", consent=True)
    assert result["fallback"]["reason"] == "gemini_unavailable"
    assert seen["prepared"] == 0


def test_capabilities_describe_both_engines_and_expose_no_secrets(monkeypatch: Any) -> None:
    monkeypatch.setattr(UploadService, "available", staticmethod(lambda: False))
    on = UploadService(True, StubReader()).capabilities()
    assert on["enabled"] is True  # Gemini alone is enough to offer uploads
    assert on["default_engine"] == "gemini" and on["external_provider"] is True
    assert on["engines"]["ocr"]["available"] is False
    assert on["engines"]["gemini"]["consent"] == CONSENT_VALUE
    off = UploadService(False, StubReader()).capabilities()
    assert off["enabled"] is False and off["engines"]["gemini"]["available"] is False
    plain = UploadService(True, StubReader(available=False)).capabilities()
    assert plain["default_engine"] == "ocr" and plain["external_provider"] is False
    assert "key" not in str(on).lower().replace("daily_limit", "")


def test_http_layer_translates_consent_header_and_engine(monkeypatch: Any) -> None:
    captured: list[dict[str, Any]] = []

    async def read(self: Any, body: bytes, policy: Any, content_type: str, **options: Any) -> Any:
        captured.append(options)
        return {"method": "stub"}

    monkeypatch.setattr(UploadService, "read", read)
    client = TestClient(create_app(read_only=True, allow_uploads=True))
    assert client.post("/api/uploads", content=b"x", headers=PNG).status_code == 200
    client.post("/api/uploads?engine=gemini", content=b"x", headers=PNG)
    client.post(
        "/api/uploads?engine=gemini", content=b"x", headers={**PNG, CONSENT_HEADER: CONSENT_VALUE}
    )
    client.post("/api/uploads?engine=gemini", content=b"x", headers={**PNG, CONSENT_HEADER: "yes"})
    assert [(o["engine"], o["consent"]) for o in captured] == [
        ("ocr", False),
        ("gemini", False),
        ("gemini", True),
        ("gemini", False),
    ]
    assert client.post("/api/uploads?engine=openai", content=b"x", headers=PNG).status_code == 422


def test_missing_consent_returns_a_clear_400_and_does_not_call_the_provider(
    monkeypatch: Any,
) -> None:
    reader = StubReader()
    instance, _ = service(reader, monkeypatch)
    monkeypatch.setattr("receipttrace.web.UploadService", lambda enabled: instance)
    client = TestClient(create_app(read_only=True, allow_uploads=True))
    response = client.post("/api/uploads?engine=gemini", content=b"x", headers=PNG)
    assert response.status_code == 400 and response.json()["error"]["code"] == "consent_required"
    assert reader.calls == 0


def test_client_address_trusts_forwarding_only_behind_a_declared_proxy(monkeypatch: Any) -> None:
    class Fake:
        client = type("Peer", (), {"host": "10.0.0.1"})()
        headers = {"x-forwarded-for": "6.6.6.6, 203.0.113.9"}

    monkeypatch.delenv("RECEIPTTRACE_PROXY_HOPS", raising=False)
    assert client_address(Fake()) == "10.0.0.1"  # type: ignore[arg-type]
    monkeypatch.setenv("RECEIPTTRACE_PROXY_HOPS", "1")
    assert client_address(Fake()) == "203.0.113.9"  # type: ignore[arg-type]
    monkeypatch.setenv("RECEIPTTRACE_PROXY_HOPS", "9")
    assert client_address(Fake()) == "10.0.0.1"  # type: ignore[arg-type]
    monkeypatch.setenv("RECEIPTTRACE_PROXY_HOPS", "bad")
    assert client_address(Fake()) == "10.0.0.1"  # type: ignore[arg-type]


def test_every_fallback_reason_is_explained_to_the_visitor_in_both_languages() -> None:
    import re
    from pathlib import Path

    root = Path(__file__).parent.parent / "src" / "receipttrace"
    emitted = set(re.findall(r'GeminiFallback\("(\w+)"\)', (root / "upload_gemini.py").read_text()))
    assert emitted >= {"gemini_paused", "gemini_unavailable", "gemini_timeout"}
    strings = (root / "static" / "i18n.js").read_text(encoding="utf-8")
    for reason in emitted:
        assert f"upload_fallback_{reason}:" in strings, reason
