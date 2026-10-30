"""Public entry point: transient OCR enabled; persistent reviews never exposed."""

import os

import uvicorn

from receipttrace.web import create_app


def main() -> None:
    port = int(os.environ.get("PORT", "10000"))
    if not 1 <= port <= 65535:
        raise ValueError("PORT must be between 1 and 65535")
    uvicorn.run(
        create_app(read_only=True, allow_uploads=True),
        host="0.0.0.0",
        port=port,
        workers=1,
        timeout_graceful_shutdown=65,
    )


if __name__ == "__main__":
    main()
