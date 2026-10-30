"""API contract, local review, read-only mode and saved evidence integration."""

import hashlib
import shutil
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx2")
from fastapi.testclient import TestClient  # noqa: E402

from receipttrace.web import create_app  # noqa: E402

EXAMPLE = "cord-train-shard0-row0006"


def make_client(application: Any) -> TestClient:
    return TestClient(application, base_url="http://127.0.0.1")


@pytest.fixture
def client(tmp_path: Path) -> Any:
    with make_client(
        create_app(read_only=False, database=tmp_path / "reviews.sqlite3")
    ) as instance:
        yield instance


def begin(client: Any) -> dict[str, Any]:
    response = client.post("/api/reviews", json={"example_id": EXAMPLE, "method": "ocr"})
    assert response.status_code == 200
    return dict(response.json())


def test_summary_uses_full_evaluation_and_keeps_unknown_ocr_cost(client: Any) -> None:
    response = client.get("/api/summary")
    assert response.status_code == 200
    summary = response.json()
    assert summary["document_count"] == 20
    assert summary["example_count"] == 3
    assert summary["curated_examples"] is True
    assert summary["total_gain"] == 5
    assert summary["methods"]["gemini"]["metrics"]["total"]["correct"] == 19
    assert summary["methods"]["ocr"]["metrics"]["total"]["correct"] == 14
    assert summary["methods"]["ocr"]["cost_summary"] is None
    assert summary["review_enabled"] is True


@pytest.mark.parametrize("method", ["ocr", "gemini"])
def test_original_values_and_image_match_saved_evidence(client: Any, method: str) -> None:
    detail = client.get(f"/api/examples/{EXAMPLE}", params={"method": method}).json()
    assert detail["raw"]["total"] == ("62,000" if method == "ocr" else "61,799")
    assert detail["evaluation"]["total"]["expected"] == "61,799"
    image = client.get(detail["image_url"])
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/png"
    assert hashlib.sha256(image.content).hexdigest() == detail["source"]["image_sha256"]
    assert isinstance(detail["validation"]["normalized"]["total"]["value"], str)


def test_web_review_lifecycle_preserves_benchmark_and_records_history(client: Any) -> None:
    original = client.get("/api/evidence/ocr").content
    initial = begin(client)
    assert initial["review_status"] == "pending"
    assert begin(client)["review_id"] == initial["review_id"]
    path = f"/api/reviews/{initial['review_id']}"
    corrected = client.post(
        path + "/corrections",
        json={
            "expected_revision": 0,
            "correction": {
                "actor": "synthetic-test",
                "reason": "Test correction",
                "changes": [{"path": "/total", "value": "61,799"}],
            },
        },
    )
    assert corrected.status_code == 200
    result = corrected.json()
    assert result["revision"] == 1
    assert result["original_raw"]["total"] == "62,000"
    assert result["current_raw"]["total"] == "61,799"
    assert result["validation"]["normalized"]["total"]["value"] == "61799"
    blocked = client.post(
        path + "/completion",
        json={
            "expected_revision": 1,
            "completion": {"actor": "synthetic-test", "reason": "Test"},
        },
    )
    assert blocked.status_code == 400
    completed = client.post(
        path + "/completion",
        json={
            "expected_revision": 1,
            "completion": {
                "actor": "synthetic-test",
                "reason": "Unchecked calculations acknowledged",
                "acknowledge_unverified": True,
            },
        },
    )
    assert completed.status_code == 200
    assert completed.json()["review_status"] == "completed"
    assert completed.json()["arithmetic"]["status"] == "not_checked"
    assert len(completed.json()["events"]) == 2
    export = client.get(path + "/export")
    assert export.json() == completed.json()
    assert "attachment;" in export.headers["content-disposition"]
    assert export.headers["cache-control"] == "no-store"
    assert client.get("/api/evidence/ocr").content == original
    assert client.get(f"/api/examples/{EXAMPLE}").json()["raw"]["total"] == "62,000"


def test_stale_revision_returns_conflict_without_overwriting(client: Any) -> None:
    initial = begin(client)
    path = f"/api/reviews/{initial['review_id']}"
    action = {
        "expected_revision": 0,
        "correction": {
            "actor": "synthetic-test",
            "reason": "First test",
            "changes": [{"path": "/total", "value": "61,799"}],
        },
    }
    assert client.post(path + "/corrections", json=action).status_code == 200
    action["correction"]["changes"][0]["value"] = "61,800"
    response = client.post(path + "/corrections", json=action)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "revision_conflict"
    assert client.get(path).json()["current_raw"]["total"] == "61,799"
    assert client.get(path).json()["revision"] == 1


def test_default_application_disables_all_review_access(tmp_path: Path) -> None:
    database = tmp_path / "not-created.sqlite3"
    with make_client(create_app(database=database)) as readonly:
        assert readonly.get("/api/summary").json()["review_enabled"] is False
        assert (
            readonly.post("/api/reviews", json={"example_id": EXAMPLE, "method": "ocr"}).status_code
            == 403
        )
        assert readonly.get(f"/api/reviews/{uuid4()}").status_code == 403
        assert readonly.get(f"/api/reviews/{uuid4()}/export").status_code == 403
    assert not database.exists()


def test_cross_origin_and_non_json_actions_are_rejected(client: Any) -> None:
    response = client.post(
        "/api/reviews",
        json={"example_id": EXAMPLE, "method": "ocr"},
        headers={"origin": "https://unrelated.example"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "origin_rejected"
    assert (
        client.post(
            "/api/reviews", content="invalid", headers={"content-type": "text/plain"}
        ).status_code
        == 415
    )
    assert (
        client.post(
            "/api/reviews",
            json={"example_id": EXAMPLE, "method": "ocr"},
            headers={"origin": "http://127.0.0.1"},
        ).status_code
        == 200
    )


@pytest.mark.parametrize(
    "body",
    [
        {"example_id": EXAMPLE, "method": "openai"},
        {"example_id": EXAMPLE, "method": "ocr", "run": "../../.env"},
        {"example_id": EXAMPLE},
    ],
)
def test_request_contract_does_not_accept_paths_or_other_providers(
    client: Any, body: dict[str, Any]
) -> None:
    response = client.post("/api/reviews", json=body)
    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "invalid_request",
            "message": "Request fields do not match the API contract",
        }
    }


@pytest.mark.parametrize(
    "path",
    [
        "/.env",
        "/assets/../review.py",
        "/api/evidence/credentials",
        "/api/examples/unknown",
        "/api/examples/unknown/image",
    ],
)
def test_unlisted_files_and_examples_are_not_exposed(client: Any, path: str) -> None:
    assert client.get(path).status_code == 404


def test_missing_review_has_a_consistent_404(client: Any) -> None:
    response = client.get(f"/api/reviews/{uuid4()}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_corrupt_history_is_not_served_as_a_valid_review(tmp_path: Path) -> None:
    database = tmp_path / "review.sqlite3"
    with make_client(create_app(read_only=False, database=database)) as local:
        initial = begin(local)
        with sqlite3.connect(database) as connection:
            connection.execute("DROP TRIGGER reviews_update_blocked")
            connection.execute("UPDATE reviews SET result = X'00'")
        response = local.get(f"/api/reviews/{initial['review_id']}")
        assert response.status_code == 500
        assert response.json()["error"]["code"] == "integrity_error"
        assert "Traceback" not in response.text


def test_page_static_modules_and_openapi_are_available(client: Any) -> None:
    page = client.get("/")
    assert page.status_code == 200
    assert '<html lang="pt-BR">' in page.text
    assert "Content-Security-Policy" in page.headers
    for name in ("styles.css", "app.js", "i18n.js", "ui.js", "api.js", "favicon.svg"):
        assert client.get("/assets/" + name).status_code == 200
    schema = client.get("/api/openapi.json").json()
    assert "CorrectionSubmission" in schema["components"]["schemas"]
    assert "/api/reviews/{review_id}/completion" in schema["paths"]


def test_bundled_data_modification_is_detected(tmp_path: Path) -> None:
    from receipttrace import web

    source = Path(web.__file__).parent / "webdata"
    altered = tmp_path / "webdata"
    shutil.copytree(source, altered)
    (altered / "reports/gemini-development-20.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="integrity"):
        create_app(data_root=altered)


def test_serve_refuses_public_mutable_binding(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from receipttrace.cli import main

    monkeypatch.setattr("sys.argv", ["receipttrace", "serve", "--host", "0.0.0.0"])
    assert main() == 1
    assert "--read-only" in capsys.readouterr().err


def test_serve_uses_local_mode_without_starting_a_server(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import uvicorn

    from receipttrace.cli import main

    captured = {}
    monkeypatch.setattr(
        uvicorn,
        "run",
        lambda application, **kwargs: captured.update({"application": application, **kwargs}),
    )
    monkeypatch.setattr(
        "sys.argv", ["receipttrace", "serve", "--database", str(tmp_path / "review.sqlite3")]
    )
    assert main() == 0
    assert captured["host"] == "127.0.0.1"
    assert captured["port"] == 8000
    with make_client(captured["application"]) as local:
        assert local.get("/api/summary").json()["review_enabled"] is True


def test_local_review_rejects_unrelated_host_headers(client: Any) -> None:
    response = client.get("/api/summary", headers={"host": "unrelated.example"})
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "host_rejected"
