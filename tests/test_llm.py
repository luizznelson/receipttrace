"""Offline LLM tests: injected providers, explicit synthetic images, no paid requests."""

import json
from pathlib import Path

import pytest
from PIL import Image
from pydantic import ValidationError

from receipttrace.llm import Answer, decode, plan, run
from receipttrace.llm_config import LLMConfig, extraction_schema


def config(**updates: object) -> LLMConfig:
    # Prices/model are synthetic fixtures, not current provider offers.
    return LLMConfig.model_validate(
        {
            "model": "synthetic-vision-model",
            "max_requests": 2,
            "max_output_tokens": 256,
            "max_input_tokens": 1000,
            "max_budget_usd": "1",
            "input_usd_per_million": "1",
            "output_usd_per_million": "2",
            "pricing_as_of": "2026-10-28",
            **updates,
        }
    )


def images(tmp_path: Path, count: int = 1) -> Path:
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    for i in range(count):
        Image.new("RGB", (20, 20), "white").save(inputs / f"synthetic-{i}.png")
    return inputs


def answer(**response_updates: object) -> Answer:
    return Answer(
        json.dumps({"total": "1,000", "items_complete": True}),
        {
            "status": "completed",
            "model": "synthetic-vision-model-snapshot",
            "id": "synthetic-response",
            "usage": {"input_tokens": 100, "output_tokens": 30},
            "output": [],
            **response_updates,
        },
    )


class FakeProvider:
    def __init__(self, response: Answer | Exception | None = None, count: int = 100) -> None:
        self.response = response or answer()
        self.tokens = count
        self.calls = 0
        self.closed = False

    def count(self, payload: dict[str, object]) -> int:
        assert "ground_truth" not in json.dumps(payload)
        assert "input" in payload and "instructions" in payload
        return self.tokens

    def extract(self, payload: dict[str, object], max_output: int) -> Answer:
        self.calls += 1
        assert max_output == 256
        if isinstance(self.response, Exception):
            raise self.response
        return self.response

    def close(self) -> None:
        self.closed = True


def test_offline_plan_requires_no_key_or_provider(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = plan(images(tmp_path), config())
    assert result["paid_calls_made"] == 0
    assert result["estimated_cost_usd"] is None
    assert len(result["prompt_sha256"]) == 64


def test_request_limit_fails_before_any_provider_request(tmp_path: Path) -> None:
    provider = FakeProvider()
    with pytest.raises(ValueError, match="max_requests"):
        run(images(tmp_path, 2), tmp_path / "run", config(max_requests=1), provider)
    assert provider.calls == 0


def test_success_preserves_usage_and_does_not_certify_completeness(tmp_path: Path) -> None:
    provider = FakeProvider()
    output = tmp_path / "run"
    manifest = run(images(tmp_path), output, config(), provider)
    result = json.loads((output / manifest["records"][0]["file"]).read_text())
    assert result["status"] == "ok"
    assert result["validation"]["raw"]["document_id"] == "synthetic-0"
    assert result["validation"]["raw"]["items_complete"] is False
    assert result["response"]["model"] == "synthetic-vision-model-snapshot"
    assert result["estimated_cost_usd"] == "0.00016"
    assert provider.closed


def test_budget_prevents_inference(tmp_path: Path) -> None:
    provider = FakeProvider()
    manifest = run(images(tmp_path), tmp_path / "run", config(max_budget_usd="0.00001"), provider)
    assert provider.calls == 0
    record = json.loads((tmp_path / "run" / manifest["records"][0]["file"]).read_text())
    assert record["error_type"] == "BudgetReservationExceeded"


def test_token_limit_prevents_inference(tmp_path: Path) -> None:
    provider = FakeProvider(count=1001)
    run(images(tmp_path), tmp_path / "run", config(), provider)
    assert provider.calls == 0


def test_uncertain_request_halts_without_retry_or_secret_logging(tmp_path: Path) -> None:
    provider = FakeProvider(RuntimeError("private-token-should-never-be-recorded"))
    output = tmp_path / "run"
    manifest = run(images(tmp_path, 2), output, config(), provider)
    assert provider.calls == 1
    assert manifest["cost_summary"]["requests_with_unknown_usage"] == 1
    assert all(row["status"] == "error" for row in manifest["records"])
    assert "private-token" not in "".join(p.read_text() for p in output.glob("*.json"))


@pytest.mark.parametrize(
    "response",
    [
        answer(status="incomplete"),
        answer(output=[{"content": [{"type": "refusal", "refusal": "synthetic refusal"}]}]),
        Answer('{"total": 0.1}', answer().response),
        Answer("not-json", answer().response),
    ],
)
def test_incomplete_refusal_and_invalid_contracts_fail(response: Answer) -> None:
    with pytest.raises(ValueError):
        decode(response, "synthetic-local-id")


def test_unknown_usage_halts_next_request(tmp_path: Path) -> None:
    provider = FakeProvider(answer(usage=None))
    result = run(images(tmp_path, 2), tmp_path / "run", config(), provider)
    assert provider.calls == 1
    assert result["cost_summary"]["requests_with_unknown_usage"] == 1


def test_all_schema_properties_are_required_and_defaults_removed() -> None:
    schema = extraction_schema()
    assert "document_id" not in schema["properties"]
    for model in [schema, *schema["$defs"].values()]:
        assert set(model["required"]) == set(model["properties"])
        assert model["additionalProperties"] is False
    assert '"default"' not in json.dumps(schema)


@pytest.mark.parametrize("value", ["NaN", "Infinity", "0", "-1", "not-a-number"])
def test_invalid_budget_rejected(value: str) -> None:
    with pytest.raises(ValidationError):
        config(max_budget_usd=value)


def test_unconfigured_live_run_never_creates_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    output = tmp_path / "run"
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        run(images(tmp_path), output, config())
    assert not output.exists()


def test_comparison_requires_same_sample_and_denominators(tmp_path: Path) -> None:
    import json

    from receipttrace.data import write_json
    from receipttrace.evaluation import compare_reports

    reference = {
        "sample_manifest_sha256": "synthetic-sample",
        "evaluation_version": "1",
        "document_count": 1,
        "documents": [{"id": "fixture", "image_sha256": "same-image"}],
        "metrics": {"total": {"annotated_documents": 1, "correct": 0}},
        "latency": {"p50_seconds": 1},
    }
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, reference)
    changed = json.loads(json.dumps(reference))
    changed["metrics"]["total"]["correct"] = 1
    write_json(candidate, changed)
    result = compare_reports(baseline, candidate, tmp_path / "comparison.json")
    assert result["metrics"]["total"]["correct_difference"] == 1
    changed["sample_manifest_sha256"] = "different-sample"
    write_json(candidate, changed)
    with pytest.raises(ValueError, match="same sample"):
        compare_reports(baseline, candidate, tmp_path / "invalid.json")


def test_cli_offline_plan_and_generic_evaluation_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from receipttrace.cli import main

    inputs = images(tmp_path)
    conf = tmp_path / "config.json"
    conf.write_text(config().model_dump_json(), encoding="utf-8")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    output = tmp_path / "plan.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "receipttrace",
            "plan-llm",
            "--inputs",
            str(inputs),
            "--config",
            str(conf),
            "--output",
            str(output),
        ],
    )
    assert main() == 0
    assert json.loads(output.read_text())["paid_calls_made"] == 0
    capsys.readouterr()
    monkeypatch.setattr("sys.argv", ["receipttrace", "evaluate-extraction", "--help"])
    with pytest.raises(SystemExit) as stopped:
        main()
    assert stopped.value.code == 0


def test_gemini_quota_halts_the_batch_without_fallback(tmp_path: Path) -> None:
    from receipttrace.gemini import GeminiQuotaExceeded

    class QuotaProvider(FakeProvider):
        counts = 0

        def count(self, payload: dict[str, object]) -> int:
            self.counts += 1
            raise GeminiQuotaExceeded("synthetic quota")

    provider = QuotaProvider()
    manifest = run(images(tmp_path, 2), tmp_path / "run", config(), provider)
    assert provider.counts == 1
    assert provider.calls == 0
    assert all(row["status"] == "error" for row in manifest["records"])
