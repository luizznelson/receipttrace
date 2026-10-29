"""Gemini Free Tier REST adapter. Never falls back to a paid provider."""

from typing import Any

from receipttrace.credentials import api_key
from receipttrace.llm import Answer
from receipttrace.llm_config import LLMConfig


class GeminiQuotaExceeded(ValueError):
    """A quota response stops the batch without retries or provider fallback."""


class GeminiFreeTierUnavailable(ValueError):
    """Project cannot use free inference; never upgrade billing automatically."""


class GeminiModelUnavailable(ValueError):
    """Selected model is unavailable for this account."""


class GeminiSchemaTooComplex(ValueError):
    """Provider rejected the structured-output grammar; fix schema before retrying."""


class GeminiProvider:
    def __init__(self, config: LLMConfig) -> None:
        if not config.free_tier_confirmed:
            raise ValueError(
                "Confirm a Gemini Free Tier project with billing disabled in configuration"
            )
        key = api_key("GEMINI_API_KEY")
        try:
            import httpx
        except ImportError as error:
            raise RuntimeError("Install: uv sync --locked --extra gemini") from error
        self.config = config
        self.client = httpx.Client(
            base_url="https://generativelanguage.googleapis.com/v1beta/",
            headers={"x-goog-api-key": key},
            timeout=180,
            follow_redirects=False,
        )

    def body(self, payload: dict[str, Any], max_output: int) -> dict[str, Any]:
        return {
            **payload,
            "generation_config": {**payload["generation_config"], "max_output_tokens": max_output},
        }

    def counting_body(self, payload: dict[str, Any]) -> dict[str, Any]:
        # countTokens still uses GenerateContent representation. Record actual usage separately.
        parts = []
        for part in payload["input"]:
            if part["type"] == "text":
                parts.append({"text": part["text"]})
            elif part["type"] == "image":
                parts.append({"inlineData": {"mimeType": part["mime_type"], "data": part["data"]}})
            else:
                raise ValueError("Unsupported counting input")
        return {
            "generateContentRequest": {
                "model": f"models/{self.config.model}",
                "contents": [{"role": "user", "parts": parts}],
                "systemInstruction": {"parts": [{"text": payload["system_instruction"]}]},
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "responseJsonSchema": payload["response_format"]["schema"],
                },
            }
        }

    @staticmethod
    def check_response(response: Any) -> None:
        if response.status_code == 429:
            raise GeminiQuotaExceeded("Gemini quota exhausted")
        if response.status_code == 404:
            raise GeminiModelUnavailable("Gemini model unavailable for this account")
        if response.status_code == 400:
            try:
                message = str(response.json().get("error", {}).get("message", "")).lower()
            except ValueError:
                message = ""
            if "too many states" in message:
                raise GeminiSchemaTooComplex("Gemini output schema is too complex")
        if response.status_code == 403:
            try:
                message = str(response.json().get("error", {}).get("message", "")).lower()
            except ValueError:
                message = ""
            if "free tier is not available" in message:
                raise GeminiFreeTierUnavailable("Gemini Free Tier unavailable for this project")
        response.raise_for_status()

    def count(self, payload: dict[str, Any]) -> int:
        response = self.client.post(
            f"models/{self.config.model}:countTokens", json=self.counting_body(payload)
        )
        self.check_response(response)
        count = response.json().get("totalTokens")
        if not isinstance(count, int) or isinstance(count, bool):
            raise ValueError("Invalid Gemini token count")
        return count

    def extract(self, payload: dict[str, Any], max_output: int) -> Answer:
        response = self.client.post("interactions", json=self.body(payload, max_output))
        self.check_response(response)
        original = response.json()
        text = "".join(
            part.get("text", "")
            for step in original.get("steps", [])
            if step.get("type") == "model_output"
            for part in step.get("content", [])
            if part.get("type") == "text"
        )
        usage = original.get("usage", {})
        input_tokens = usage.get("total_input_tokens")
        total_tokens = usage.get("total_tokens")
        normalized_usage = None
        if type(input_tokens) is int and type(total_tokens) is int and total_tokens >= input_tokens:
            normalized_usage = {
                "input_tokens": input_tokens,
                "output_tokens": total_tokens - input_tokens,
            }
        return Answer(
            text,
            {
                "status": original.get("status", "incomplete"),
                "model": original.get("model"),
                "id": original.get("id"),
                "usage": normalized_usage,
                "output": [],
                "gemini_response": original,
            },
        )

    def close(self) -> None:
        self.client.close()
