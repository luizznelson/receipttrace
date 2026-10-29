"""Review behavior, source preservation, concurrent edits and audit integrity."""

import hashlib
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from threading import Barrier
from typing import Any

import pytest
from pydantic import ValidationError

from receipttrace.cli_serialization import decimal_json
from receipttrace.domain import RawItem, RawReceipt, report
from receipttrace.review import (
    CompletionRequest,
    Correction,
    CorrectionRequest,
    ReviewConflict,
    ReviewIntegrityError,
    ReviewStore,
)


def source_run(folder: Path, *, status: str = "ok", raw: RawReceipt | None = None) -> Path:
    folder.mkdir()
    raw = raw or RawReceipt(
        document_id="synthetic-review-case",
        total="62,000",
        subtotal="56,181",
        tax="5,618",
        items=[RawItem(description="Synthetic item", children=[RawItem(amount="1,000")])],
    )
    result: dict[str, Any] = {
        "id": raw.document_id,
        "image_sha256": "a" * 64,
        "status": status,
        "seconds": 1.0,
    }
    if status != "error":
        result["validation"] = report(raw, "idr-grouped", Decimal(0))
    payload = json.dumps(result, default=decimal_json).encode()
    (folder / "result.json").write_bytes(payload)
    manifest = {
        "engine": {"provider": "synthetic-test"},
        "records": [
            {
                "id": raw.document_id,
                "file": "result.json",
                "sha256": hashlib.sha256(payload).hexdigest(),
                "status": status,
            }
        ],
    }
    (folder / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return folder


def correction(path: str = "/total", value: Any = "61,799") -> CorrectionRequest:
    return CorrectionRequest(
        actor="synthetic-reviewer",
        reason="Compared with the source image",
        changes=[Correction(path=path, value=value)],
    )


@pytest.fixture
def opened(tmp_path: Path) -> tuple[ReviewStore, dict[str, Any], Path]:
    run = source_run(tmp_path / "source")
    store = ReviewStore(tmp_path / "review.sqlite3")
    return store, store.start(run, "synthetic-review-case"), run


def test_start_preserves_source_and_does_not_claim_approval(
    opened: tuple[ReviewStore, dict[str, Any], Path],
) -> None:
    store, state, run = opened
    original = (run / "result.json").read_bytes()
    assert state["extraction_status"] == "ok"
    assert state["review_status"] == "pending"
    assert state["arithmetic"]["status"] == "not_checked"
    assert state["arithmetic"]["passed"] == 0
    assert state["original_raw"] == state["current_raw"]
    assert state["revision"] == 0
    assert not state["events"]
    with sqlite3.connect(store.database) as connection:
        assert connection.execute("SELECT result FROM reviews").fetchone()[0] == original
    assert store.start(run, "synthetic-review-case")["review_id"] == state["review_id"]


def test_correction_survives_reopening_and_preserves_before_after(
    opened: tuple[ReviewStore, dict[str, Any], Path],
) -> None:
    store, state, run = opened
    source = {path.name: path.read_bytes() for path in run.iterdir()}
    changed = store.correct(state["review_id"], 0, correction())
    assert changed["revision"] == 1
    assert changed["review_status"] == "pending"
    assert changed["original_raw"]["total"] == "62,000"
    assert changed["current_raw"]["total"] == "61,799"
    assert changed["events"][0]["changes"] == [
        {"path": "/total", "before": "62,000", "after": "61,799"}
    ]
    event = changed["events"][0]
    assert event["actor"] == "synthetic-reviewer"
    assert event["reason"] == "Compared with the source image"
    assert datetime.fromisoformat(event["created_at_utc"]).utcoffset() == timedelta(0)
    assert changed["source"] == state["source"]
    assert changed["head_sha256"] != state["head_sha256"]
    assert ReviewStore(store.database).view(state["review_id"]) == changed
    assert {path.name: path.read_bytes() for path in run.iterdir()} == source


def test_nested_fields_and_whole_item_lists_can_be_corrected(
    opened: tuple[ReviewStore, dict[str, Any], Path],
) -> None:
    store, state, _ = opened
    changed = store.correct(
        state["review_id"], 0, correction("/items/0/children/0/amount", "2,000")
    )
    assert changed["current_raw"]["items"][0]["children"][0]["amount"] == "2,000"
    changed = store.correct(
        state["review_id"],
        1,
        correction("/items", [{"description": "Replacement item", "amount": "56,181"}]),
    )
    assert changed["current_raw"]["items"][0]["description"] == "Replacement item"
    assert changed["original_raw"]["items"][0]["description"] == "Synthetic item"


@pytest.mark.parametrize(
    "path,value",
    [
        ("/document_id", "another-document"),
        ("/unknown", "value"),
        ("total", "61,799"),
        ("/", "value"),
        ("/items/-1/amount", "1"),
        ("/items/01/amount", "1"),
        ("/items/9/amount", "1"),
        ("/items/0/not_a_field", "1"),
        ("/items/0/description/part", "1"),
        ("/total", 61799),
        ("/items_complete", "true"),
        ("/items", [{"amount": 1.2}]),
        ("/total", "62,000"),
    ],
)
def test_invalid_correction_is_atomic(
    opened: tuple[ReviewStore, dict[str, Any], Path],
    path: str,
    value: Any,
) -> None:
    store, state, _ = opened
    with pytest.raises(ValueError):
        store.correct(state["review_id"], 0, correction(path, value))
    assert store.view(state["review_id"]) == state


@pytest.mark.parametrize(
    "paths",
    [("/total", "/total"), ("/items", "/items/0/amount"), ("/items/0/amount", "/items")],
)
def test_duplicate_and_overlapping_changes_are_rejected(
    opened: tuple[ReviewStore, dict[str, Any], Path],
    paths: tuple[str, str],
) -> None:
    store, state, _ = opened
    request = CorrectionRequest(
        actor="reviewer",
        reason="Test overlap",
        changes=[Correction(path=path, value="1") for path in paths],
    )
    with pytest.raises(ValueError, match="overlapping"):
        store.correct(state["review_id"], 0, request)
    assert store.view(state["review_id"]) == state


def test_failed_second_change_does_not_persist_first_change(
    opened: tuple[ReviewStore, dict[str, Any], Path],
) -> None:
    store, state, _ = opened
    request = CorrectionRequest(
        actor="reviewer",
        reason="Two corrections",
        changes=[Correction(path="/total", value="61,799"), Correction(path="/tax", value=5618)],
    )
    with pytest.raises(ValidationError):
        store.correct(state["review_id"], 0, request)
    assert store.view(state["review_id"]) == state


@pytest.mark.parametrize("field", ["actor", "reason"])
def test_actor_and_reason_cannot_be_blank(field: str) -> None:
    values = {"actor": "reviewer", "reason": "Compared image", field: "  "}
    with pytest.raises(ValidationError):
        CompletionRequest.model_validate(values)


def test_completion_requires_acknowledgement_and_is_independent_of_arithmetic(
    opened: tuple[ReviewStore, dict[str, Any], Path],
) -> None:
    store, state, _ = opened
    with pytest.raises(ValueError, match="unverified"):
        store.complete(state["review_id"], 0, CompletionRequest(actor="reviewer", reason="Checked"))
    completed = store.complete(
        state["review_id"],
        0,
        CompletionRequest(
            actor="reviewer",
            reason="Checked; calculations unavailable",
            acknowledge_unverified=True,
        ),
    )
    assert completed["review_status"] == "completed"
    assert completed["extraction_status"] == "ok"
    assert completed["arithmetic"]["status"] == "not_checked"
    assert completed["original_raw"] == completed["current_raw"]
    assert completed["events"][0]["changes"] == []
    with pytest.raises(ValueError, match="already"):
        store.complete(
            state["review_id"],
            1,
            CompletionRequest(actor="reviewer", reason="Again", acknowledge_unverified=True),
        )
    reopened = store.correct(state["review_id"], 1, correction())
    assert reopened["review_status"] == "pending"
    assert [event["kind"] for event in reopened["events"]] == ["completed", "corrected"]
    completed_again = store.complete(
        state["review_id"],
        2,
        CompletionRequest(
            actor="second-reviewer", reason="Checked new value", acknowledge_unverified=True
        ),
    )
    assert completed_again["review_status"] == "completed"
    assert completed_again["revision"] == 3


@pytest.mark.parametrize("value", ["100", "unreadable"])
def test_findings_require_explicit_acknowledgement(tmp_path: Path, value: str) -> None:
    raw = RawReceipt(
        document_id="synthetic-review-case",
        subtotal="100",
        discount="0",
        tax="10",
        service="0",
        total=value,
    )
    store = ReviewStore(tmp_path / "reviews.sqlite3")
    state = store.start(source_run(tmp_path / "source", raw=raw), raw.document_id)
    with pytest.raises(ValueError, match="findings"):
        store.complete(
            state["review_id"],
            0,
            CompletionRequest(actor="reviewer", reason="Checked", acknowledge_unverified=True),
        )
    result = store.complete(
        state["review_id"],
        0,
        CompletionRequest(
            actor="reviewer",
            reason="Recorded exception; not financial approval",
            acknowledge_findings=True,
            acknowledge_unverified=True,
        ),
    )
    assert result["review_status"] == "completed"
    assert result["arithmetic"]["status"] == "findings"


def test_all_passing_calculations_do_not_complete_review(tmp_path: Path) -> None:
    raw = RawReceipt(
        document_id="synthetic-review-case",
        subtotal="100",
        discount="0",
        tax="10",
        service="0",
        total="110",
        items_complete=True,
        items=[
            RawItem(
                description="Synthetic", quantity="1", unit_price="100", amount="100", discount="0"
            )
        ],
    )
    store = ReviewStore(tmp_path / "review.sqlite3")
    state = store.start(source_run(tmp_path / "source", raw=raw), raw.document_id)
    assert state["arithmetic"]["status"] == "passed"
    assert state["review_status"] == "pending"
    result = store.complete(
        state["review_id"], 0, CompletionRequest(actor="reviewer", reason="Checked")
    )
    assert result["review_status"] == "completed"


@pytest.mark.parametrize("status", ["error", "empty"])
def test_failed_or_empty_extraction_cannot_be_marked_reviewed(tmp_path: Path, status: str) -> None:
    store = ReviewStore(tmp_path / "reviews.sqlite3")
    state = store.start(source_run(tmp_path / "source", status=status), "synthetic-review-case")
    assert state["extraction_status"] == status
    assert state["review_status"] == "unavailable"
    assert state["arithmetic"]["status"] == "unavailable"
    assert state["current_raw"] is None
    with pytest.raises(ValueError, match="unavailable"):
        store.correct(state["review_id"], 0, correction())
    with pytest.raises(ValueError, match="unavailable"):
        store.complete(
            state["review_id"],
            0,
            CompletionRequest(actor="reviewer", reason="Test", acknowledge_unverified=True),
        )


def test_two_simultaneous_edits_cannot_overwrite_each_other(
    opened: tuple[ReviewStore, dict[str, Any], Path],
) -> None:
    store, state, _ = opened
    barrier = Barrier(2)

    def edit(value: str) -> str:
        barrier.wait(timeout=10)
        try:
            ReviewStore(store.database).correct(state["review_id"], 0, correction(value=value))
        except ReviewConflict:
            return "conflict"
        return "saved"

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(edit, ["61,799", "61,800"]))
    assert sorted(outcomes) == ["conflict", "saved"]
    assert store.view(state["review_id"])["revision"] == 1


def test_source_mutation_and_manifest_path_escape_are_rejected(tmp_path: Path) -> None:
    run = source_run(tmp_path / "source")
    store = ReviewStore(tmp_path / "reviews.sqlite3")
    (run / "result.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="checksum"):
        store.start(run, "synthetic-review-case")
    assert not store.database.exists()
    manifest = json.loads((run / "manifest.json").read_bytes())
    manifest["records"][0]["file"] = "../outside.json"
    (run / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="escapes"):
        store.start(run, "synthetic-review-case")


def test_database_prevents_update_and_delete_of_evidence(
    opened: tuple[ReviewStore, dict[str, Any], Path],
) -> None:
    store, state, _ = opened
    store.correct(state["review_id"], 0, correction())
    with sqlite3.connect(store.database) as connection:
        for sql in (
            "UPDATE reviews SET result = X'00'",
            "DELETE FROM reviews",
            "UPDATE review_events SET body = '{}'",
            "DELETE FROM review_events",
        ):
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                connection.execute(sql)


@pytest.mark.parametrize("target", ["snapshot", "event"])
def test_integrity_verification_detects_modified_storage(
    opened: tuple[ReviewStore, dict[str, Any], Path],
    target: str,
) -> None:
    store, state, _ = opened
    store.correct(state["review_id"], 0, correction())
    with sqlite3.connect(store.database) as connection:
        if target == "snapshot":
            connection.execute("DROP TRIGGER reviews_update_blocked")
            connection.execute("UPDATE reviews SET result = X'00'")
        else:
            connection.execute("DROP TRIGGER review_events_update_blocked")
            body = json.loads(connection.execute("SELECT body FROM review_events").fetchone()[0])
            body["reason"] = "Modified reason"
            connection.execute("UPDATE review_events SET body = ?", (json.dumps(body),))
    with pytest.raises(ReviewIntegrityError):
        store.view(state["review_id"])
    with pytest.raises(ReviewIntegrityError):
        store.correct(state["review_id"], 1, correction(value="61,800"))


def test_snapshot_remains_usable_after_source_is_removed(
    opened: tuple[ReviewStore, dict[str, Any], Path],
) -> None:
    store, state, run = opened
    for file in run.iterdir():
        file.unlink()
    assert store.view(state["review_id"]) == state


def test_unrelated_database_is_not_reinitialized(tmp_path: Path) -> None:
    database = tmp_path / "other.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE existing (value TEXT)")
    store = ReviewStore(database)
    run = source_run(tmp_path / "source")
    with pytest.raises(ValueError, match="unrelated"):
        store.start(run, "synthetic-review-case")
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT name FROM sqlite_master").fetchall() == [("existing",)]
