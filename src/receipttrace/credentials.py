"""Read only an explicitly named credential from the process or local .env."""

import os
from pathlib import Path

from dotenv import dotenv_values


def api_key(name: str) -> str:
    if name not in {"GEMINI_API_KEY", "OPENAI_API_KEY"}:
        raise ValueError("Unsupported credential name")
    value: str | None
    if name in os.environ:
        value = os.environ[name]
    else:
        # Explicit cwd only: never search parent directories or expand variable references.
        value = dotenv_values(Path.cwd() / ".env", encoding="utf-8-sig", interpolate=False).get(
            name
        )
    if not value or not value.strip():
        raise ValueError(f"Configure {name} in the project .env file or process environment")
    return value.strip()
