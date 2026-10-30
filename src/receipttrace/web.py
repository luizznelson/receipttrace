"""Same-origin FastAPI application for saved examples and local receipt review."""

import json
import sqlite3
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, Literal
from uuid import UUID

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from receipttrace.cli_serialization import decimal_json
from receipttrace.demo_catalog import DemoCatalog, ExampleNotFound, Method
from receipttrace.review import (
    CompletionRequest,
    CorrectionRequest,
    ReviewConflict,
    ReviewIntegrityError,
    ReviewNotFound,
    ReviewStore,
)


class ExactJSONResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        return json.dumps(
            content, ensure_ascii=False, allow_nan=False, default=decimal_json
        ).encode("utf-8")


class StartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    example_id: str = Field(min_length=1, max_length=200)
    method: Method


class CorrectionSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    expected_revision: int = Field(ge=0)
    correction: CorrectionRequest


class CompletionSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    expected_revision: int = Field(ge=0)
    completion: CompletionRequest


def _error(status: int, code: str, message: str) -> ExactJSONResponse:
    return ExactJSONResponse({"error": {"code": code, "message": message}}, status_code=status)


def create_app(
    *,
    read_only: bool = True,
    database: Path = Path("runs/reviews.sqlite3"),
    data_root: Path | None = None,
) -> FastAPI:
    """Default factory is read-only; local `receipttrace serve` explicitly enables review."""
    package = Path(__file__).parent
    catalog = DemoCatalog(data_root or package / "webdata")
    store = ReviewStore(database)
    app = FastAPI(
        title="ReceiptTrace API",
        version="0.1.0",
        docs_url=None,
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )

    @app.middleware("http")
    async def same_origin(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if not read_only and request.url.hostname not in {"127.0.0.1", "localhost", "::1"}:
            return _error(403, "host_rejected", "Local review requires a loopback host")
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            if read_only:
                return _error(403, "read_only", "This instance is a read-only demonstration")
            origin = request.headers.get("origin")
            if origin is not None and origin.rstrip("/") != str(request.base_url).rstrip("/"):
                return _error(403, "origin_rejected", "Cross-origin changes are not allowed")
            if request.headers.get("content-type", "").split(";")[0] != "application/json":
                return _error(415, "json_required", "Use an application/json request")
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; "
            "connect-src 'self'; object-src 'none'; base-uri 'none'; "
            "frame-ancestors 'none'; form-action 'self'"
        )
        if request.url.path.startswith("/api/reviews"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, error: RequestValidationError) -> Response:
        return _error(422, "invalid_request", "Request fields do not match the API contract")

    @app.exception_handler(ExampleNotFound)
    @app.exception_handler(ReviewNotFound)
    async def missing(request: Request, error: ValueError) -> Response:
        return _error(404, "not_found", "Requested example or review was not found")

    @app.exception_handler(ReviewConflict)
    async def conflict(request: Request, error: ReviewConflict) -> Response:
        return _error(
            409, "revision_conflict", "Review changed; reload and check the current revision"
        )

    @app.exception_handler(ReviewIntegrityError)
    async def integrity(request: Request, error: ReviewIntegrityError) -> Response:
        return _error(500, "integrity_error", "Review evidence could not be verified")

    @app.exception_handler(ValueError)
    async def rejected(request: Request, error: ValueError) -> Response:
        return _error(
            400, "invalid_action", "Check the fields, reason and required acknowledgements"
        )

    @app.exception_handler(sqlite3.Error)
    async def storage(request: Request, error: sqlite3.Error) -> Response:
        return _error(503, "storage_unavailable", "Local review storage is unavailable")

    def require_review() -> None:
        if read_only:
            raise PermissionError("Read-only instance")

    @app.exception_handler(PermissionError)
    async def readonly(request: Request, error: PermissionError) -> Response:
        return _error(403, "read_only", "This instance is a read-only demonstration")

    @app.get("/api/health")
    def health() -> Response:
        return ExactJSONResponse(
            {"status": "ok", "mode": "read_only" if read_only else "local_review"}
        )

    @app.get("/api/summary")
    def summary() -> Response:
        return ExactJSONResponse({**catalog.summary(), "review_enabled": not read_only})

    @app.get("/api/examples")
    def examples() -> Response:
        return ExactJSONResponse(catalog.examples())

    @app.get("/api/examples/{example_id}")
    def example(example_id: str, method: Literal["ocr", "gemini"] = "ocr") -> Response:
        return ExactJSONResponse(catalog.detail(example_id, method))

    @app.get("/api/examples/{example_id}/image")
    def image(example_id: str) -> Response:
        return FileResponse(catalog.image(example_id), media_type="image/png")

    @app.get("/api/evidence/{name}")
    def evidence(name: str) -> Response:
        files = {
            "ocr": catalog.root / "reports/ocr-baseline.json",
            "gemini": catalog.root / "reports/gemini-development-20.json",
            "comparison": catalog.root / "reports/ocr-vs-gemini-development-20.json",
            "sample": catalog.root / "reports/cord-inspection.manifest.json",
            "attribution": catalog.root / "ATTRIBUTION.md",
        }
        if name not in files:
            raise ExampleNotFound("Unknown evidence file")
        return FileResponse(
            files[name], media_type="text/plain" if name == "attribution" else "application/json"
        )

    @app.post("/api/reviews")
    def start_review(body: StartRequest) -> Response:
        require_review()
        catalog.require_example(body.example_id)
        return ExactJSONResponse(store.start(catalog.run(body.method), body.example_id))

    @app.get("/api/reviews/{review_id}")
    def review(review_id: UUID) -> Response:
        require_review()
        if not database.exists():
            raise ReviewNotFound("Review not found")
        return ExactJSONResponse(store.view(str(review_id)))

    @app.post("/api/reviews/{review_id}/corrections")
    def correct(review_id: UUID, body: CorrectionSubmission) -> Response:
        require_review()
        if not database.exists():
            raise ReviewNotFound("Review not found")
        return ExactJSONResponse(
            store.correct(str(review_id), body.expected_revision, body.correction)
        )

    @app.post("/api/reviews/{review_id}/completion")
    def complete(review_id: UUID, body: CompletionSubmission) -> Response:
        require_review()
        if not database.exists():
            raise ReviewNotFound("Review not found")
        return ExactJSONResponse(
            store.complete(str(review_id), body.expected_revision, body.completion)
        )

    @app.get("/api/reviews/{review_id}/export")
    def export(review_id: UUID) -> Response:
        response = review(review_id)
        response.headers["Content-Disposition"] = (
            f'attachment; filename="receipttrace-review-{review_id}.json"'
        )
        return response

    @app.get("/", include_in_schema=False)
    def index() -> Response:
        return FileResponse(package / "static/index.html", media_type="text/html")

    app.mount("/assets", StaticFiles(directory=package / "static"), name="assets")
    return app
