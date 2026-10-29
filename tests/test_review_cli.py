"""Exercise the review workflow through the public CLI, without network or keys."""

import json
from pathlib import Path

import pytest

from receipttrace.cli import main


def source(tmp_path: Path) -> Path:
    import hashlib

    folder = tmp_path / "extraction"
    folder.mkdir()
    result = {
        "id": "synthetic-cli-review",
        "status": "ok",
        "image_sha256": "b" * 64,
        "validation": {
            "raw": {"document_id": "synthetic-cli-review", "total": "62,000"},
            "numeric_policy": "idr-grouped",
            "tolerance": "0",
        },
    }
    payload = json.dumps(result).encode()
    (folder / "receipt.json").write_bytes(payload)
    (folder / "manifest.json").write_text(
        json.dumps(
            {
                "records": [
                    {
                        "id": result["id"],
                        "file": "receipt.json",
                        "sha256": hashlib.sha256(payload).hexdigest(),
                        "status": "ok",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return folder


def test_cli_review_end_to_end(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    folder = source(tmp_path)
    database = tmp_path / "review.sqlite3"
    original = (folder / "receipt.json").read_bytes()

    def invoke(*arguments: str) -> tuple[int, str]:
        monkeypatch.setattr("sys.argv", ["receipttrace", *arguments, "--database", str(database)])
        code = main()
        captured = capsys.readouterr()
        return code, captured.out if code == 0 else captured.err

    code, output = invoke(
        "review-start", "--run", str(folder), "--document-id", "synthetic-cli-review"
    )
    assert code == 0
    initial = json.loads(output)
    review_id = initial["review_id"]
    request = tmp_path / "correction.json"
    request.write_text(
        json.dumps(
            {
                "actor": "synthetic-reviewer",
                "reason": "Compared source",
                "changes": [{"path": "/total", "value": "61,799"}],
            }
        ),
        encoding="utf-8",
    )
    code, output = invoke(
        "review-correct",
        "--review-id",
        review_id,
        "--expected-revision",
        "0",
        "--request",
        str(request),
    )
    assert code == 0
    assert json.loads(output)["current_raw"]["total"] == "61,799"
    code, output = invoke(
        "review-correct",
        "--review-id",
        review_id,
        "--expected-revision",
        "0",
        "--request",
        str(request),
    )
    assert code == 1
    assert "current 1" in output
    completion = tmp_path / "completion.json"
    completion.write_text(
        json.dumps(
            {
                "actor": "synthetic-reviewer",
                "reason": "Checked extraction; arithmetic unavailable",
                "acknowledge_unverified": True,
            }
        ),
        encoding="utf-8",
    )
    code, output = invoke(
        "review-complete",
        "--review-id",
        review_id,
        "--expected-revision",
        "1",
        "--request",
        str(completion),
    )
    assert code == 0
    complete = json.loads(output)
    assert complete["review_status"] == "completed"
    assert complete["arithmetic"]["status"] == "not_checked"
    code, output = invoke("review-show", "--review-id", review_id)
    assert code == 0
    assert json.loads(output) == complete
    assert (folder / "receipt.json").read_bytes() == original


def test_cli_does_not_create_a_store_just_to_read_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    database = tmp_path / "missing.sqlite3"
    monkeypatch.setattr(
        "sys.argv",
        ["receipttrace", "review-show", "--database", str(database), "--review-id", "missing"],
    )
    assert main() == 1
    assert "Error:" in capsys.readouterr().err
    assert not database.exists()


def test_invalid_request_file_does_not_modify_review(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from receipttrace.review import ReviewStore

    database = tmp_path / "review.sqlite3"
    store = ReviewStore(database)
    state = store.start(source(tmp_path), "synthetic-cli-review")
    request = tmp_path / "invalid.json"
    request.write_text('{"actor":"reviewer","reason":"test","changes":[]}', encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        [
            "receipttrace",
            "review-correct",
            "--database",
            str(database),
            "--review-id",
            state["review_id"],
            "--expected-revision",
            "0",
            "--request",
            str(request),
        ],
    )
    assert main() == 1
    assert "Error:" in capsys.readouterr().err
    assert store.view(state["review_id"]) == state
