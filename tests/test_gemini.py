"""Gemini HTTP contract tests with synthetic credentials and no network."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

httpx = pytest.importorskip("httpx")

from receipttrace.gemini import GeminiProvider  # noqa: E402
from receipttrace.llm import decode, request  # noqa: E402
from receipttrace.llm_config import LLMConfig, extraction_schema  # noqa: E402


def configuration(**changes: object) -> LLMConfig:
    return LLMConfig.model_validate(
        {
            "provider": "gemini-free",
            "model": "gemini-3.5-flash-lite",
            "thinking_level": "minimal",
            "free_tier_confirmed": True,
            "max_requests": 20,
            "max_input_tokens": 20000,
            "max_output_tokens": 2048,
            "max_budget_usd": "0",
            "input_usd_per_million": "0",
            "output_usd_per_million": "0",
            "pricing_as_of": "2026-10-28",
            **changes,
        }
    )


def test_free_config_does_not_allow_paid_rates_or_unknown_models() -> None:
    assert configuration().estimate(100, 100) == 0
    with pytest.raises(ValidationError):
        configuration(input_usd_per_million="1")
    with pytest.raises(ValidationError):
        configuration(model="gemini-4-argon")


def test_free_tier_must_be_confirmed_before_client_creation() -> None:
    with pytest.raises(ValueError, match="billing disabled"):
        GeminiProvider(configuration(free_tier_confirmed=False))


def test_missing_key_cannot_trigger_a_paid_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-unusable-key")
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        GeminiProvider(configuration())


def test_gemini_count_image_schema_and_usage(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-not-a-real-key")
    observed: list[httpx.Request] = []

    def handle(req: httpx.Request) -> httpx.Response:
        observed.append(req)
        assert req.headers["x-goog-api-key"] == "synthetic-not-a-real-key"
        assert "key=" not in str(req.url)
        if req.url.path.endswith(":countTokens"):
            return httpx.Response(200, json={"totalTokens": 100})
        assert req.url.path.endswith("/interactions")
        return httpx.Response(
            200,
            json={
                "id": "synthetic-response",
                "model": "synthetic-model-version",
                "status": "completed",
                "steps": [
                    {"type": "thought", "summary": [{"type": "text", "text": "not final output"}]},
                    {
                        "type": "model_output",
                        "content": [{"type": "text", "text": '{"total":"1,000"}'}],
                    },
                ],
                "usage": {
                    "total_input_tokens": 100,
                    "total_output_tokens": 20,
                    "total_thought_tokens": 10,
                    "total_tokens": 130,
                },
            },
        )

    provider = GeminiProvider(configuration())
    provider.client.close()
    provider.client = httpx.Client(
        base_url="https://generativelanguage.googleapis.com/v1beta/",
        headers={"x-goog-api-key": "synthetic-not-a-real-key"},
        transport=httpx.MockTransport(handle),
    )
    try:
        payload = request(b"synthetic-image", configuration())
        assert provider.count(payload) == 100
        answer = provider.extract(payload, 2048)
        assert answer.text == '{"total":"1,000"}'
        assert answer.response["usage"] == {"input_tokens": 100, "output_tokens": 30}
        assert decode(answer, "local-id").document_id == "local-id"
        counted = json.loads(observed[0].content)["generateContentRequest"]
        generated = json.loads(observed[1].content)
        assert (
            counted["contents"][0]["parts"][1]["inlineData"]["data"]
            == generated["input"][1]["data"]
        )
        assert counted["systemInstruction"]["parts"][0]["text"] == generated["system_instruction"]
        assert (
            counted["generationConfig"]["responseJsonSchema"]
            == generated["response_format"]["schema"]
        )
        assert generated["generation_config"]["thinking_level"] == "minimal"
        assert generated["generation_config"]["max_output_tokens"] == 2048
        assert generated["store"] is False
        assert "tools" not in generated
        assert generated["response_format"]["mime_type"] == "application/json"
    finally:
        provider.close()


def test_optional_recursion_matches_gemini_schema_constraints() -> None:
    schema = extraction_schema("gemini-free")
    assert "children" not in schema["$defs"]["RawItem"]["required"]
    assert "children" in schema["$defs"]["RawItem"]["properties"]


def test_quota_error_does_not_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-not-a-real-key")
    calls = 0

    def handle(req: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(429, json={"error": {"message": "synthetic quota exceeded"}})

    provider = GeminiProvider(configuration())
    provider.client.close()
    provider.client = httpx.Client(
        base_url="https://generativelanguage.googleapis.com/v1beta/",
        transport=httpx.MockTransport(handle),
    )
    try:
        with pytest.raises(ValueError, match="quota"):
            provider.extract(request(b"fixture", configuration()), 2048)
        assert calls == 1
    finally:
        provider.close()


@pytest.mark.parametrize(
    "status,message,expected",
    [
        (
            403,
            "The Gemini API free tier is not available for this project. private-fixture",
            "GeminiFreeTierUnavailable",
        ),
        (404, "Unavailable model private-fixture", "GeminiModelUnavailable"),
    ],
)
def test_project_and_model_errors_are_actionable_without_echoing_body(
    status: int, message: str, expected: str
) -> None:
    response = httpx.Response(status, json={"error": {"message": message}})
    with pytest.raises(ValueError) as error:
        GeminiProvider.check_response(response)
    assert type(error.value).__name__ == expected
    assert "private-fixture" not in str(error.value)


def test_rejects_unsupported_thinking_level_for_flash() -> None:
    with pytest.raises(ValidationError):
        configuration(model="gemini-3.8-flash", thinking_level="minimal")


def test_transport_avoids_large_array_grammar_limits_but_domain_remains_bounded() -> None:
    from receipttrace.domain import RawItem, RawReceipt

    wire = extraction_schema("gemini-free")
    assert '"maxItems"' not in json.dumps(wire)
    with pytest.raises(ValidationError):
        RawReceipt.model_validate({"document_id": "fixture", "items": [{}] * 1001})
    with pytest.raises(ValidationError):
        RawItem.model_validate({"children": [{}] * 101})


def test_schema_complexity_error_is_actionable() -> None:
    response = httpx.Response(
        400, json={"error": {"message": "Schema has too many states for serving"}}
    )
    with pytest.raises(ValueError) as error:
        GeminiProvider.check_response(response)
    assert type(error.value).__name__ == "GeminiSchemaTooComplex"
