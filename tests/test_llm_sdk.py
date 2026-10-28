"""SDK contract tests with HTTPX MockTransport: no request can leave this process."""

import json

import pytest

httpx = pytest.importorskip("httpx")
openai = pytest.importorskip("openai")

from receipttrace.llm import OpenAIProvider, request  # noqa: E402
from receipttrace.llm_config import LLMConfig  # noqa: E402


def configuration() -> LLMConfig:
    return LLMConfig(
        model="synthetic-test-model",
        max_requests=1,
        max_output_tokens=256,
        max_input_tokens=1000,
        max_budget_usd="1",
        input_usd_per_million="1",
        output_usd_per_million="1",
        pricing_as_of="2026-10-28",
    )


def test_sdk_image_schema_and_usage_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-not-a-real-key")
    observed: list[dict[str, object]] = []

    def handle(req: httpx.Request) -> httpx.Response:
        body = json.loads(req.content)
        observed.append(body)
        if req.url.path.endswith("/input_tokens"):
            return httpx.Response(
                200, json={"object": "response.input_tokens", "input_tokens": 123}
            )
        return httpx.Response(
            200,
            json={
                "id": "synthetic-response",
                "object": "response",
                "created_at": 0,
                "model": "synthetic-snapshot",
                "status": "completed",
                "error": None,
                "output": [
                    {
                        "type": "message",
                        "id": "synthetic-msg",
                        "role": "assistant",
                        "status": "completed",
                        "content": [
                            {"type": "output_text", "text": '{"total":"1,000"}', "annotations": []}
                        ],
                    }
                ],
                "usage": {
                    "input_tokens": 123,
                    "output_tokens": 20,
                    "total_tokens": 143,
                    "input_tokens_details": {"cached_tokens": 0},
                    "output_tokens_details": {"reasoning_tokens": 0},
                },
                "parallel_tool_calls": False,
                "tools": [],
                "tool_choice": "auto",
            },
        )

    provider = OpenAIProvider()
    provider.client.close()
    provider.client = openai.OpenAI(
        api_key="synthetic-not-a-real-key",
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handle)),
    )
    try:
        payload = request(b"synthetic-image-bytes", configuration())
        assert provider.count(payload) == 123
        answer = provider.extract(payload, 256)
        assert answer.text == '{"total":"1,000"}'
        assert answer.response["usage"]["total_tokens"] == 143
        assert observed[1]["store"] is False
        assert observed[1]["max_output_tokens"] == 256
        assert observed[0]["input"] == observed[1]["input"]
        assert observed[0]["text"] == observed[1]["text"]
        assert "ground_truth" not in json.dumps(observed)
    finally:
        provider.close()


def test_sdk_does_not_retry_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-not-a-real-key")
    calls = 0

    def handle(req: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ReadTimeout("synthetic timeout", request=req)

    provider = OpenAIProvider()
    provider.client.close()
    provider.client = openai.OpenAI(
        api_key="synthetic-not-a-real-key",
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handle)),
    )
    try:
        with pytest.raises(openai.APITimeoutError):
            provider.extract(request(b"fixture", configuration()), 256)
        assert calls == 1
    finally:
        provider.close()
