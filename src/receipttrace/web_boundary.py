"""ASGI boundary: bounded input, uniform response headers and redacted error IDs."""

import asyncio
import json
import logging
from uuid import uuid4

from starlette.datastructures import MutableHeaders
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

MAX_BODY_BYTES = 256 * 1024
BODY_TIMEOUT_SECONDS = 10.0
logger = logging.getLogger("receipttrace.web")


class BodyTooLarge(Exception):
    """Request body exceeded the limit before reaching validation or storage."""


def failure(status: int, code: str, message: str) -> Response:
    return Response(
        json.dumps({"error": {"code": code, "message": message}}),
        status_code=status,
        media_type="application/json",
    )


async def read_body(receive: Receive, limit: int) -> bytes | None:
    chunks = []
    size = 0
    while True:
        message = await receive()
        if message["type"] == "http.disconnect":
            return None
        chunk = message.get("body", b"")
        size += len(chunk)
        if size > limit:
            raise BodyTooLarge
        chunks.append(chunk)
        if not message.get("more_body", False):
            return b"".join(chunks)


class WebBoundary:
    def __init__(
        self,
        app: ASGIApp,
        *,
        read_only: bool,
        max_body_bytes: int = MAX_BODY_BYTES,
        body_timeout_seconds: float = BODY_TIMEOUT_SECONDS,
    ) -> None:
        self.app = app
        self.read_only = read_only
        self.max_body_bytes = max_body_bytes
        self.body_timeout_seconds = body_timeout_seconds

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request_id = uuid4().hex
        started = False

        async def protected_send(message: Message) -> None:
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
                headers = MutableHeaders(scope=message)
                headers["X-Request-ID"] = request_id
                headers["X-Content-Type-Options"] = "nosniff"
                headers["Referrer-Policy"] = "no-referrer"
                headers["Content-Security-Policy"] = (
                    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; "
                    "connect-src 'self'; object-src 'none'; base-uri 'none'; "
                    "frame-ancestors 'none'; form-action 'self'"
                )
                if scope.get("path", "").startswith("/api/"):
                    headers["Cache-Control"] = "no-store"
            await send(message)

        try:
            request = Request(scope)
            if not self.read_only and request.url.hostname not in {"127.0.0.1", "localhost", "::1"}:
                await failure(403, "host_rejected", "Local review requires a loopback host")(
                    scope, receive, protected_send
                )
                return
            if scope["method"] in {"POST", "PUT", "PATCH", "DELETE"}:
                if self.read_only:
                    await failure(403, "read_only", "This instance is read-only")(
                        scope, receive, protected_send
                    )
                    return
                origin = request.headers.get("origin")
                if origin is not None and origin.rstrip("/") != str(request.base_url).rstrip("/"):
                    await failure(403, "origin_rejected", "Cross-origin changes are not allowed")(
                        scope, receive, protected_send
                    )
                    return
                if (
                    request.headers.get("content-type", "").split(";")[0].strip().lower()
                    != "application/json"
                ):
                    await failure(415, "json_required", "Use an application/json request")(
                        scope, receive, protected_send
                    )
                    return
                declared = request.headers.get("content-length")
                if declared is not None:
                    if len(declared) > 20 or not declared.isascii() or not declared.isdecimal():
                        await failure(400, "invalid_request", "Invalid content length")(
                            scope, receive, protected_send
                        )
                        return
                    if int(declared) > self.max_body_bytes:
                        raise BodyTooLarge
                try:
                    body = await asyncio.wait_for(
                        read_body(receive, self.max_body_bytes), timeout=self.body_timeout_seconds
                    )
                except TimeoutError:
                    await failure(408, "body_timeout", "Request body was not received in time")(
                        scope, receive, protected_send
                    )
                    return
                if body is None:
                    return
                delivered = False

                async def replay() -> Message:
                    nonlocal delivered
                    if not delivered:
                        delivered = True
                        return {"type": "http.request", "body": body, "more_body": False}
                    return await receive()

                await self.app(scope, replay, protected_send)
            else:
                await self.app(scope, receive, protected_send)
        except BodyTooLarge:
            await failure(413, "request_too_large", "Request exceeds the 256 KiB limit")(
                scope, receive, protected_send
            )
        except Exception as error:
            # Do not log bodies, credentials, notes, URLs or exception messages.
            logger.error("request_id=%s exception_type=%s", request_id, type(error).__name__)
            if started:
                raise RuntimeError(f"Response stream failed; request_id={request_id}") from None
            await failure(
                500, "internal_error", "Unexpected failure; use the request ID for support"
            )(scope, receive, protected_send)
