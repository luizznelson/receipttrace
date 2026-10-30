"""Local receipt review: immutable source snapshots and append-only events."""

import copy
import hashlib
import json
import re
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal, cast
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator

from receipttrace.cli_serialization import decimal_json
from receipttrace.domain import RawReceipt, report, summarize_validation
from receipttrace.money import POLICIES, NumberPolicy


class ReviewNotFound(ValueError):
    """The requested review is not in this store."""


class ReviewStorageError(ValueError):
    """Database configuration or schema is incompatible with this store."""


class ReviewConflict(ValueError):
    """The caller edited a revision that is no longer current."""


class ReviewIntegrityError(ValueError):
    """Stored evidence or event history does not match its recorded hashes."""


class ReviewAction(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    actor: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=2000)

    @field_validator("actor", "reason")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Actor and reason must contain non-whitespace text")
        return value


class Correction(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    path: str = Field(min_length=2, max_length=500)
    value: JsonValue


class CorrectionRequest(ReviewAction):
    changes: list[Correction] = Field(min_length=1, max_length=100)


class CompletionRequest(ReviewAction):
    acknowledge_findings: bool = False
    acknowledge_unverified: bool = False


class ChangeRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    path: str
    before: JsonValue
    after: JsonValue


class ReviewEvent(ReviewAction):
    revision: int = Field(ge=1)
    kind: Literal["corrected", "completed"]
    created_at_utc: str
    previous_hash: str
    changes: list[ChangeRecord] = Field(default_factory=list, max_length=100)
    acknowledge_findings: bool = False
    acknowledge_unverified: bool = False

    @field_validator("created_at_utc")
    @classmethod
    def utc_time(cls, value: str) -> str:
        parsed = datetime.fromisoformat(value)
        offset = parsed.utcoffset()
        if offset is None or offset.total_seconds() != 0:
            raise ValueError("Event timestamp must be UTC")
        return value


def _json(value: object) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=decimal_json
    )


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _source(result_bytes: bytes, manifest_bytes: bytes, document_id: str) -> dict[str, Any]:
    """Verify only saved extraction evidence; never open annotations or source images."""
    result = json.loads(result_bytes)
    manifest = json.loads(manifest_bytes)
    if not isinstance(result, dict) or not isinstance(manifest, dict):
        raise ValueError("Source result and manifest must be JSON objects")
    records = manifest.get("records")
    if not isinstance(records, list) or not all(isinstance(row, dict) for row in records):
        raise ValueError("Source manifest must contain extraction records")
    ids = [row.get("id") for row in records]
    if not all(isinstance(value, str) for value in ids) or len(set(ids)) != len(ids):
        raise ValueError("Source manifest contains invalid or duplicate IDs")
    matched = [row for row in records if row["id"] == document_id]
    if len(matched) != 1:
        raise ValueError("Document not found in the source manifest")
    record = matched[0]
    if record.get("sha256") != _digest(result_bytes):
        raise ValueError("Source extraction checksum mismatch")
    if result.get("id") != document_id or result.get("status") != record.get("status"):
        raise ValueError("Source result and manifest disagree")
    image_hash = result.get("image_sha256")
    if not isinstance(image_hash, str) or not re.fullmatch(r"[a-f0-9]{64}", image_hash):
        raise ValueError("Source result requires an image SHA-256")
    status = result["status"]
    if status not in ("ok", "empty", "error"):
        raise ValueError("Unsupported extraction status")
    raw = None
    policy = None
    tolerance = None
    if status == "ok":
        validation = result.get("validation")
        if not isinstance(validation, dict):
            raise ValueError("Successful extraction requires structured validation data")
        raw = RawReceipt.model_validate(validation.get("raw"))
        if raw.document_id != document_id:
            raise ValueError("Receipt document ID does not match the extraction")
        policy = validation.get("numeric_policy")
        if policy not in POLICIES:
            raise ValueError("Unsupported source numeric policy")
        if not isinstance(validation.get("tolerance"), str):
            raise ValueError("Source tolerance must be an explicit decimal string")
        tolerance = Decimal(validation["tolerance"])
        # Recompute rather than trusting cached flags from the saved result.
        report(raw, policy, tolerance)
    return {
        "raw": raw,
        "policy": policy,
        "tolerance": tolerance,
        "extraction_status": status,
        "image_sha256": image_hash,
        "engine": manifest.get("engine"),
    }


def _location(data: dict[str, Any], path: str) -> tuple[Any, str | int]:
    """Replace existing JSON Pointer locations, never metadata or document identity."""
    parts = path.split("/")
    if len(parts) < 2 or parts[0] or any(not part or "~" in part for part in parts[1:]):
        raise ValueError("Use an existing receipt field as a JSON Pointer")
    if parts[1] == "document_id":
        raise ValueError("Document identity cannot be corrected")
    current: Any = data
    for index, part in enumerate(parts[1:]):
        if isinstance(current, dict) and part in current:
            key: str | int = part
        elif (
            isinstance(current, list)
            and re.fullmatch(r"0|[1-9][0-9]*", part)
            and int(part) < len(current)
        ):
            key = int(part)
        else:
            raise ValueError("Correction path does not identify an existing receipt field")
        if index == len(parts) - 2:
            return current, key
        current = current[key]
    raise ValueError("Invalid correction path")


def _correct(raw: RawReceipt, changes: list[Correction]) -> tuple[RawReceipt, list[ChangeRecord]]:
    paths = [change.path for change in changes]
    for index, path in enumerate(paths):
        if any(path == other or path.startswith(other + "/") for other in paths[:index]):
            raise ValueError("Duplicate or overlapping correction paths")
        if any(other.startswith(path + "/") for other in paths[:index]):
            raise ValueError("Duplicate or overlapping correction paths")
    data = copy.deepcopy(raw.model_dump(mode="json"))
    records = []
    for change in changes:
        parent, key = _location(data, change.path)
        before = parent[key]
        if _json(before) == _json(change.value):
            raise ValueError("Correction must change the original field value")
        records.append(ChangeRecord(path=change.path, before=before, after=change.value))
        parent[key] = copy.deepcopy(change.value)
    return RawReceipt.model_validate(data), records


def _completion(
    raw: RawReceipt | None,
    policy: NumberPolicy | None,
    tolerance: Decimal | None,
    action: CompletionRequest,
) -> None:
    if raw is None or policy is None or tolerance is None:
        raise ValueError("Extraction is unavailable for review; obtain a successful extraction")
    validation = report(raw, policy, tolerance)
    if validation["has_findings"] and not action.acknowledge_findings:
        raise ValueError("Completion requires explicit acknowledgement of validation findings")
    if validation["has_skipped_checks"] and not action.acknowledge_unverified:
        raise ValueError("Completion requires explicit acknowledgement of unverified calculations")


_TABLES = (
    """CREATE TABLE reviews (
        review_id TEXT PRIMARY KEY,
        source_hash TEXT NOT NULL,
        manifest_hash TEXT NOT NULL,
        metadata TEXT NOT NULL,
        snapshot_hash TEXT NOT NULL,
        result BLOB NOT NULL,
        manifest BLOB NOT NULL,
        UNIQUE(source_hash, manifest_hash)
    )""",
    """CREATE TABLE review_events (
        review_id TEXT NOT NULL REFERENCES reviews(review_id),
        revision INTEGER NOT NULL CHECK(revision > 0),
        body TEXT NOT NULL,
        event_hash TEXT NOT NULL,
        PRIMARY KEY(review_id, revision)
    )""",
)


class ReviewStore:
    """Local SQLite store. Actor names are declarations, not authenticated identities."""

    def __init__(self, database: Path) -> None:
        self.database = database

    @staticmethod
    def _version(connection: sqlite3.Connection) -> int:
        return cast(int, connection.execute("PRAGMA user_version").fetchone()[0])

    @contextmanager
    def _write(self) -> Iterator[sqlite3.Connection]:
        self.database.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database, isolation_level=None, timeout=5)
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("BEGIN IMMEDIATE")
            version = self._version(connection)
            if version == 0:
                if connection.execute("SELECT name FROM sqlite_master").fetchone() is not None:
                    raise ReviewStorageError("Refusing to initialize an unrelated database")
                for statement in _TABLES:
                    connection.execute(statement)
                for table in ("reviews", "review_events"):
                    for operation in ("UPDATE", "DELETE"):
                        connection.execute(
                            f"CREATE TRIGGER {table}_{operation.lower()}_blocked "
                            f"BEFORE {operation} ON {table} BEGIN "
                            "SELECT RAISE(ABORT, 'Review evidence is append-only'); END"
                        )
                connection.execute("PRAGMA user_version = 1")
            elif version != 1:
                raise ReviewStorageError("Unsupported review database version")
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def start(self, run: Path, document_id: str) -> dict[str, Any]:
        manifest_bytes = (run / "manifest.json").read_bytes()
        manifest = json.loads(manifest_bytes)
        if not isinstance(manifest, dict) or not isinstance(manifest.get("records"), list):
            raise ValueError("Invalid extraction manifest")
        records = [
            row
            for row in manifest["records"]
            if isinstance(row, dict) and row.get("id") == document_id
        ]
        if len(records) != 1 or not isinstance(records[0].get("file"), str):
            raise ValueError("Document must have exactly one extraction result")
        source_path = (run / records[0]["file"]).resolve()
        if not source_path.is_relative_to(run.resolve()):
            raise ValueError("Source result path escapes its run directory")
        result_bytes = source_path.read_bytes()
        _source(result_bytes, manifest_bytes, document_id)
        source_hash, manifest_hash = _digest(result_bytes), _digest(manifest_bytes)
        with self._write() as connection:
            existing = connection.execute(
                "SELECT review_id FROM reviews WHERE source_hash = ? AND manifest_hash = ?",
                (source_hash, manifest_hash),
            ).fetchone()
            if existing is not None:
                return self._view(connection, existing["review_id"])
            review_id = str(uuid4())
            metadata = _json(
                {
                    "schema_version": 1,
                    "review_id": review_id,
                    "document_id": document_id,
                    "created_at_utc": _now(),
                    "source_hash": source_hash,
                    "manifest_hash": manifest_hash,
                }
            )
            connection.execute(
                "INSERT INTO reviews VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    review_id,
                    source_hash,
                    manifest_hash,
                    metadata,
                    _digest(metadata.encode()),
                    result_bytes,
                    manifest_bytes,
                ),
            )
            return self._view(connection, review_id)

    def view(self, review_id: str) -> dict[str, Any]:
        uri = self.database.resolve().as_uri() + "?mode=ro"
        connection = sqlite3.connect(uri, uri=True, isolation_level=None, timeout=5)
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("BEGIN")
            if self._version(connection) != 1:
                raise ReviewStorageError("Unsupported review database version")
            return self._view(connection, review_id)
        finally:
            connection.close()

    def _view(self, connection: sqlite3.Connection, review_id: str) -> dict[str, Any]:
        stored = connection.execute(
            "SELECT * FROM reviews WHERE review_id = ?", (review_id,)
        ).fetchone()
        if stored is None:
            raise ReviewNotFound("Review not found")
        try:
            return self._materialize(connection, stored)
        except (ValueError, KeyError, TypeError, AttributeError) as error:
            raise ReviewIntegrityError(
                "Review snapshot or event history failed verification"
            ) from error

    @staticmethod
    def _materialize(connection: sqlite3.Connection, stored: sqlite3.Row) -> dict[str, Any]:
        metadata = json.loads(stored["metadata"])
        if (
            _digest(stored["metadata"].encode()) != stored["snapshot_hash"]
            or _digest(stored["result"]) != stored["source_hash"]
            or _digest(stored["manifest"]) != stored["manifest_hash"]
            or any(
                metadata[key] != stored[key]
                for key in ("review_id", "source_hash", "manifest_hash")
            )
            or metadata["schema_version"] != 1
        ):
            raise ValueError("Snapshot checksum mismatch")
        source = _source(stored["result"], stored["manifest"], metadata["document_id"])
        raw: RawReceipt | None = source["raw"]
        original = raw.model_dump(mode="json") if raw else None
        status = "pending" if raw else "unavailable"
        events = []
        previous_hash = stored["snapshot_hash"]
        policy, tolerance = source["policy"], source["tolerance"]
        rows = connection.execute(
            "SELECT * FROM review_events WHERE review_id = ? ORDER BY revision",
            (stored["review_id"],),
        ).fetchall()
        for revision, row in enumerate(rows, start=1):
            event = ReviewEvent.model_validate_json(row["body"])
            if (
                event.revision != revision
                or row["revision"] != revision
                or event.previous_hash != previous_hash
                or _digest(row["body"].encode()) != row["event_hash"]
                or raw is None
            ):
                raise ValueError("Event checksum, sequence or extraction mismatch")
            if event.kind == "corrected":
                if not event.changes or event.acknowledge_findings or event.acknowledge_unverified:
                    raise ValueError("Invalid correction event")
                updated, calculated = _correct(
                    raw,
                    [Correction(path=change.path, value=change.after) for change in event.changes],
                )
                if calculated != event.changes:
                    raise ValueError("Correction does not match its prior values")
                raw, status = updated, "pending"
            else:
                if event.changes or status != "pending":
                    raise ValueError("Invalid completion event")
                _completion(
                    raw,
                    policy,
                    tolerance,
                    CompletionRequest(
                        actor=event.actor,
                        reason=event.reason,
                        acknowledge_findings=event.acknowledge_findings,
                        acknowledge_unverified=event.acknowledge_unverified,
                    ),
                )
                status = "completed"
            events.append({**event.model_dump(mode="json"), "event_hash": row["event_hash"]})
            previous_hash = row["event_hash"]
        validation = report(raw, policy, tolerance) if raw is not None else None
        return {
            "schema_version": 1,
            "review_id": stored["review_id"],
            "document_id": metadata["document_id"],
            "image_sha256": source["image_sha256"],
            "created_at_utc": metadata["created_at_utc"],
            "revision": len(events),
            "extraction_status": source["extraction_status"],
            "review_status": status,
            "arithmetic": summarize_validation(validation),
            "original_raw": original,
            "current_raw": raw.model_dump(mode="json") if raw is not None else None,
            "validation": validation,
            "events": events,
            "source": {
                "result_sha256": stored["source_hash"],
                "manifest_sha256": stored["manifest_hash"],
                "snapshot_sha256": stored["snapshot_hash"],
                "engine": source["engine"],
                "numeric_policy": policy,
                "tolerance": str(tolerance) if tolerance is not None else None,
            },
            "head_sha256": previous_hash,
        }

    @staticmethod
    def _check_revision(state: dict[str, Any], expected_revision: int) -> None:
        if type(expected_revision) is not int or expected_revision < 0:
            raise ValueError("Expected revision must be a nonnegative integer")
        if state["revision"] != expected_revision:
            raise ReviewConflict(
                f"Review changed: expected {expected_revision}, current {state['revision']}"
            )
        if state["review_status"] == "unavailable":
            raise ValueError("Extraction is unavailable for review; obtain a successful extraction")

    @staticmethod
    def _append(connection: sqlite3.Connection, review_id: str, event: ReviewEvent) -> None:
        body = _json(event.model_dump(mode="json"))
        connection.execute(
            "INSERT INTO review_events VALUES (?, ?, ?, ?)",
            (review_id, event.revision, body, _digest(body.encode())),
        )

    def correct(
        self, review_id: str, expected_revision: int, request: CorrectionRequest
    ) -> dict[str, Any]:
        with self._write() as connection:
            state = self._view(connection, review_id)
            self._check_revision(state, expected_revision)
            _, changes = _correct(RawReceipt.model_validate(state["current_raw"]), request.changes)
            event = ReviewEvent(
                revision=expected_revision + 1,
                kind="corrected",
                created_at_utc=_now(),
                previous_hash=state["head_sha256"],
                actor=request.actor,
                reason=request.reason,
                changes=changes,
            )
            self._append(connection, review_id, event)
            return self._view(connection, review_id)

    def complete(
        self, review_id: str, expected_revision: int, request: CompletionRequest
    ) -> dict[str, Any]:
        with self._write() as connection:
            state = self._view(connection, review_id)
            self._check_revision(state, expected_revision)
            if state["review_status"] == "completed":
                raise ValueError("This revision has already been reviewed")
            _completion(
                RawReceipt.model_validate(state["current_raw"]),
                cast(NumberPolicy, state["source"]["numeric_policy"]),
                Decimal(state["source"]["tolerance"]),
                request,
            )
            event = ReviewEvent(
                revision=expected_revision + 1,
                kind="completed",
                created_at_utc=_now(),
                previous_hash=state["head_sha256"],
                actor=request.actor,
                reason=request.reason,
                acknowledge_findings=request.acknowledge_findings,
                acknowledge_unverified=request.acknowledge_unverified,
            )
            self._append(connection, review_id, event)
            return self._view(connection, review_id)
