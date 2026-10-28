"""Gemini Free Tier REST adapter. Never falls back to a paid provider."""

import os
from typing import Any

from receipttrace.llm import Answer
from receipttrace.llm_config import LLMConfig


class GeminiQuotaExceeded(ValueError):
    """A quota response stops the batch without retries or provider fallback."""


class GeminiProvider:
    def __init__(self, config: LLMConfig) -> None:
        if not config.free_tier_confirmed:
            raise ValueError(
                "Confirm a Gemini Free Tier project with billing disabled in configuration"
            )
        if not os.environ.get("GEMINI_API_KEY"):
            raise ValueError("Configure GEMINI_API_KEY locally, never in chat or Git")
        try:
            import httpx
        except ImportError as error:
            raise RuntimeError("Install: uv sync --locked --extra gemini") from error
        self.config = config
        self.client = httpx.Client(
            base_url="https://generativelanguage.googleapis.com/v1beta/",
            headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]},
            timeout=60,
            follow_redirects=False,
        )

    def body(self, payload: dict[str, Any], max_output: int) -> dict[str, Any]:
        return {
            **payload,
            "generationConfig": {**payload["generationConfig"], "maxOutputTokens": max_output},
        }

    def count(self, payload: dict[str, Any]) -> int:
        body = self.body(payload, self.config.max_output_tokens)
        # Count the same full generation request, including system instruction and schema.
        response = self.client.post(
            f"models/{self.config.model}:countTokens",
            json={"generateContentRequest": {"model": f"models/{self.config.model}", **body}},
        )
        if response.status_code == 429:
            raise GeminiQuotaExceeded("Gemini quota exhausted")
        response.raise_for_status()
        count = response.json().get("totalTokens")
        if not isinstance(count, int) or isinstance(count, bool):
            raise ValueError("Invalid Gemini token count")
        return count

    def extract(self, payload: dict[str, Any], max_output: int) -> Answer:
        response = self.client.post(
            f"models/{self.config.model}:generateContent", json=self.body(payload, max_output)
        )
        if response.status_code == 429:
            raise GeminiQuotaExceeded("Gemini quota exhausted")
        response.raise_for_status()
        original = response.json()
        candidates = original.get("candidates", [])
        candidate = candidates[0] if candidates else {}
        text = "".join(
            part.get("text", "")
            for part in candidate.get("content", {}).get("parts", [])
            if not part.get("thought", False)
        )
        usage = original.get("usageMetadata", {})
        input_tokens = usage.get("promptTokenCount")
        output_tokens = usage.get("totalTokenCount")
        normalized_usage = None
        if (
            type(input_tokens) is int
            and type(output_tokens) is int
            and output_tokens >= input_tokens
        ):
            normalized_usage = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens - input_tokens,
            }
        return Answer(
            text,
            {
                "status": "completed" if candidate.get("finishReason") == "STOP" else "incomplete",
                "model": original.get("modelVersion"),
                "id": original.get("responseId"),
                "usage": normalized_usage,
                "output": [],
                "gemini_response": original,
            },
        )

    def close(self) -> None:
        self.client.close()
