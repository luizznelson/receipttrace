"""Same-origin FastAPI application for saved examples and local receipt review."""

import json
import sqlite3
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal, cast
from uuid import UUID

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from receipttrace.cli_serialization import decimal_json
from receipttrace.demo_catalog import DemoCatalog, DemoIntegrityError, ExampleNotFound, Method
from receipttrace.domain import RawReceipt, report
from receipttrace.money import NumberPolicy
from receipttrace.review import (
    CompletionRequest,
    CorrectionRequest,
    ReviewConflict,
    ReviewIntegrityError,
    ReviewNotFound,
    ReviewStorageError,
    ReviewStore,
)
from receipttrace.uploads import UploadRejected, UploadService
from receipttrace.web_boundary import WebBoundary


class ReadOnlyReviewError(Exception):
    """Public instances do not expose local review storage."""


class ReviewActionRejected(ValueError):
    """A valid HTTP request failed a review-domain precondition."""


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


class UploadedFields(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    document_id: str = Field(min_length=1, max_length=200)
    currency: None = None
    items: list[Any] = Field(default_factory=list, max_length=0)
    items_complete: Literal[False] = False
    total: str | None = Field(default=None, max_length=64)
    subtotal: str | None = Field(default=None, max_length=64)
    tax: str | None = Field(default=None, max_length=64)
    service: str | None = Field(default=None, max_length=64)
    discount: str | None = Field(default=None, max_length=64)


class UploadValidationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    raw: UploadedFields
    policy: Literal["brl-grouped", "usd-grouped", "idr-grouped"]


def _error(status: int, code: str, message: str) -> ExactJSONResponse:
    return ExactJSONResponse({"error": {"code": code, "message": message}}, status_code=status)


def create_app(
    *,
    read_only: bool = True,
    allow_uploads: bool = False,
    database: Path = Path("runs/reviews.sqlite3"),
    data_root: Path | None = None,
) -> FastAPI:
    """Default factory is read-only; local `receipttrace serve` explicitly enables review."""
    package = Path(__file__).parent
    catalog = DemoCatalog(data_root or package / "webdata")
    store = ReviewStore(database)
    uploads = UploadService(allow_uploads)
    app = FastAPI(
        title="ReceiptTrace API",
        version="0.1.0",
        docs_url=None,
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )

    app.add_middleware(WebBoundary, read_only=read_only, allow_uploads=allow_uploads)

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

    @app.exception_handler(ReviewActionRejected)
    async def rejected(request: Request, error: ValueError) -> Response:
        return _error(
            400, "invalid_action", "Check the fields, reason and required acknowledgements"
        )

    @app.exception_handler(ReviewStorageError)
    @app.exception_handler(sqlite3.Error)
    async def storage(request: Request, error: sqlite3.Error) -> Response:
        return _error(503, "storage_unavailable", "Local review storage is unavailable")

    def require_review() -> None:
        if read_only:
            raise ReadOnlyReviewError("Read-only instance")

    @app.exception_handler(ReadOnlyReviewError)
    async def readonly(request: Request, error: ReadOnlyReviewError) -> Response:
        return _error(403, "read_only", "This instance is a read-only demonstration")

    @app.exception_handler(DemoIntegrityError)
    async def demo_integrity(request: Request, error: DemoIntegrityError) -> Response:
        return _error(500, "integrity_error", "Demonstration evidence could not be verified")

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, error: StarletteHTTPException) -> Response:
        codes = {404: "not_found", 405: "method_not_allowed"}
        response = _error(
            error.status_code, codes.get(error.status_code, "request_rejected"), "Request rejected"
        )
        if error.status_code == 405 and error.headers and "Allow" in error.headers:
            response.headers["Allow"] = error.headers["Allow"]
        return response

    def review_action(operation: Callable[[], dict[str, Any]]) -> Response:
        try:
            return ExactJSONResponse(operation())
        except ReviewConflict, ReviewIntegrityError, ReviewNotFound, ReviewStorageError:
            raise
        except ValueError as error:
            raise ReviewActionRejected("Review action rejected") from error

    @app.exception_handler(UploadRejected)
    async def upload_error(request: Request, error: UploadRejected) -> Response:
        response = _error(error.status, error.code, "Image processing could not be completed")
        if error.status == 429:
            response.headers["Retry-After"] = "60"
        return response

    @app.post("/api/uploads/validate")
    def validate_upload(body: UploadValidationRequest) -> Response:
        if not allow_uploads:
            raise UploadRejected("ocr_unavailable", 503)
        raw = RawReceipt.model_validate(body.raw.model_dump())
        return ExactJSONResponse(report(raw, body.policy, Decimal(0)))

    @app.get("/api/uploads/capabilities")
    def upload_capabilities() -> Response:
        return ExactJSONResponse(uploads.capabilities())

    @app.post(
        "/api/uploads",
        summary="Read a temporary receipt image using local OCR",
        responses={
            413: {"description": "Image exceeds the byte limit"},
            429: {"description": "OCR capacity or shared rate limit reached"},
            503: {"description": "OCR unavailable or failed"},
            504: {"description": "OCR worker exceeded its time limit"},
        },
        openapi_extra={
            "requestBody": {
                "required": True,
                "content": {
                    "image/png": {"schema": {"type": "string", "format": "binary"}},
                    "image/jpeg": {"schema": {"type": "string", "format": "binary"}},
                },
            }
        },
    )
    async def upload(
        request: Request,
        policy: Literal["brl-grouped", "usd-grouped", "idr-grouped"] = "brl-grouped",
    ) -> Response:
        content_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
        result = await uploads.extract(
            await request.body(), cast(NumberPolicy, policy), content_type
        )
        return ExactJSONResponse(result)

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
            "ocr": "reports/ocr-baseline.json",
            "gemini": "reports/gemini-development-20.json",
            "comparison": "reports/ocr-vs-gemini-development-20.json",
            "sample": "reports/cord-inspection.manifest.json",
            "attribution": "ATTRIBUTION.md",
        }
        if name not in files:
            raise ExampleNotFound("Unknown evidence file")
        return FileResponse(
            catalog.verified_asset(files[name]),
            media_type="text/plain" if name == "attribution" else "application/json",
        )

    @app.post("/api/reviews")
    def start_review(body: StartRequest) -> Response:
        require_review()
        catalog.require_example(body.example_id)
        catalog.detail(body.example_id, body.method)
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
        return review_action(
            lambda: store.correct(str(review_id), body.expected_revision, body.correction)
        )

    @app.post("/api/reviews/{review_id}/completion")
    def complete(review_id: UUID, body: CompletionSubmission) -> Response:
        require_review()
        if not database.exists():
            raise ReviewNotFound("Review not found")
        return review_action(
            lambda: store.complete(str(review_id), body.expected_revision, body.completion)
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
