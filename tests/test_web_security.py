"""Regression tests for request boundaries, redaction and trusted evidence."""

import asyncio
import logging
import shutil
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx2")
from fastapi.testclient import TestClient  # noqa: E402

import receipttrace.web as web  # noqa: E402
from receipttrace.web_boundary import MAX_BODY_BYTES, WebBoundary  # noqa: E402

EXAMPLE = "cord-train-shard0-row0006"


def assert_protected(response: Any, status: int, code: str) -> None:
    assert response.status_code == status
    assert response.json()["error"]["code"] == code
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert len(response.headers["x-request-id"]) == 32


@pytest.mark.parametrize("error_type", [RuntimeError, ValueError, TimeoutError, PermissionError])
def test_unexpected_failures_redact_details(tmp_path: Path, caplog: Any, error_type: Any) -> None:
    app = web.create_app(database=tmp_path / "reviews.sqlite3")

    @app.get("/api/fault")
    def fault() -> None:
        raise error_type("secret-credential-and-private-note")

    with caplog.at_level(logging.ERROR, logger="receipttrace.web"):
        response = TestClient(app).get("/api/fault")
    assert_protected(response, 500, "internal_error")
    assert "secret-credential" not in response.text + caplog.text
    assert response.headers["x-request-id"] in caplog.text


@pytest.mark.parametrize(
    ("path", "method", "kwargs", "status", "code"),
    [
        ("/api/missing", "get", {}, 404, "not_found"),
        ("/api/health", "put", {"json": {}}, 403, "read_only"),
        ("/api/reviews", "post", {"json": {}}, 403, "read_only"),
        ("/api/health", "delete", {}, 403, "read_only"),
        ("/api/reviews", "get", {}, 405, "method_not_allowed"),
    ],
)
def test_early_and_routing_errors_have_security_headers(
    tmp_path: Path, path: str, method: str, kwargs: Any, status: int, code: str
) -> None:
    response = getattr(TestClient(web.create_app(database=tmp_path / "db")), method)(path, **kwargs)
    assert_protected(response, status, code)
    if status == 405:
        assert "POST" in response.headers["allow"]
    assert not (tmp_path / "db").exists()


@pytest.mark.parametrize(
    ("headers", "content", "status", "code"),
    [
        ({"origin": "https://foreign.example"}, "{}", 403, "origin_rejected"),
        ({"host": "foreign.example"}, "{}", 403, "host_rejected"),
        ({"content-type": "text/plain"}, "{}", 415, "json_required"),
        ({"content-length": str(MAX_BODY_BYTES + 1)}, "{}", 413, "request_too_large"),
        ({"content-length": "-1"}, "{}", 400, "invalid_request"),
        ({"content-length": "1"}, "x" * (MAX_BODY_BYTES + 1), 413, "request_too_large"),
        ({}, "{broken", 422, "invalid_request"),
    ],
)
def test_rejected_input_never_creates_database(
    tmp_path: Path, headers: Any, content: str, status: int, code: str
) -> None:
    database = tmp_path / "db"
    client = TestClient(
        web.create_app(read_only=False, database=database), base_url="http://127.0.0.1"
    )
    response = client.post(
        "/api/reviews", content=content, headers={"content-type": "application/json", **headers}
    )
    assert_protected(response, status, code)
    assert not database.exists()


@pytest.mark.parametrize("scenario", ["timeout", "chunked_overflow", "disconnect"])
def test_asgi_input_boundary_before_route(scenario: str) -> None:
    messages: list[Any] = []
    called = False
    receives = 0

    async def downstream(scope: Any, receive: Any, send: Any) -> None:
        nonlocal called
        called = True

    async def receive() -> Any:
        nonlocal receives
        receives += 1
        if scenario == "timeout":
            await asyncio.sleep(1)
        if scenario == "disconnect":
            return {"type": "http.disconnect"}
        return {"type": "http.request", "body": b"12345", "more_body": True}

    async def send(message: Any) -> None:
        messages.append(message)

    scope = {
        "type": "http",
        "method": "POST",
        "scheme": "http",
        "path": "/api/reviews",
        "root_path": "",
        "query_string": b"",
        "server": ("127.0.0.1", 80),
        "headers": [(b"host", b"127.0.0.1"), (b"content-type", b"application/json")],
    }
    asyncio.run(
        WebBoundary(downstream, read_only=False, max_body_bytes=8, body_timeout_seconds=0.01)(
            scope, receive, send
        )
    )
    assert not called
    if scenario == "disconnect":
        assert not messages
    else:
        assert messages[0]["status"] == (408 if scenario == "timeout" else 413)
        assert receives == (1 if scenario == "timeout" else 2)


@pytest.mark.parametrize("remove", [False, True])
@pytest.mark.parametrize("asset", ["image", "extraction", "report"])
def test_tampered_or_missing_evidence_is_not_served(
    tmp_path: Path, asset: str, remove: bool
) -> None:
    root = tmp_path / "webdata"
    shutil.copytree(Path(web.__file__).parent / "webdata", root)
    app = web.create_app(data_root=root)
    names = {
        "image": f"images/{EXAMPLE}.png",
        "extraction": f"extractions/ocr/{EXAMPLE}.json",
        "report": "reports/ocr-baseline.json",
    }
    target = root / names[asset]
    assert target.is_file()
    if remove:
        target.unlink()
    else:
        target.write_bytes(b"tampered")
    routes = {
        "image": f"/api/examples/{EXAMPLE}/image",
        "extraction": f"/api/examples/{EXAMPLE}?method=ocr",
        "report": "/api/evidence/ocr",
    }
    client = TestClient(app)
    assert_protected(client.get(routes[asset]), 500, "integrity_error")
    assert_protected(client.get("/api/evidence/unknown"), 404, "not_found")
