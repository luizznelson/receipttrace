"""Image-only Responses API adapter and auditable, budget-reserved runs."""

import base64
import hashlib
import json
import platform
import subprocess
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext
from importlib.metadata import version
from importlib.resources import files
from pathlib import Path
from typing import Any, Protocol

from PIL import Image

from receipttrace.cli_serialization import decimal_json
from receipttrace.credentials import api_key
from receipttrace.data import sha256
from receipttrace.domain import RawReceipt, report
from receipttrace.llm_config import LLMConfig, extraction_schema


def prompt() -> str:
    return files("receipttrace").joinpath("prompts/extract-v1.txt").read_text(encoding="utf-8")


def request(
    image: bytes,
    config: LLMConfig,
    *,
    prompt_text: str | None = None,
    schema: dict[str, Any] | None = None,
    mime_type: str = "image/png",
) -> dict[str, Any]:
    if config.provider == "gemini-free":
        return {
            "model": config.model,
            "store": False,
            "system_instruction": prompt() if prompt_text is None else prompt_text,
            "input": [
                {"type": "text", "text": "Extract this receipt. Return null for unknown fields."},
                {
                    "type": "image",
                    "mime_type": mime_type,
                    "data": base64.b64encode(image).decode("ascii"),
                },
            ],
            "generation_config": {
                "max_output_tokens": config.max_output_tokens,
                "thinking_level": config.thinking_level,
            },
            "response_format": {
                "type": "text",
                "mime_type": "application/json",
                "schema": extraction_schema(config.provider) if schema is None else schema,
            },
        }
    return {
        "model": config.model,
        "instructions": prompt() if prompt_text is None else prompt_text,
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "Extract this receipt. Return null for unknown fields.",
                    },
                    {
                        "type": "input_image",
                        "detail": "high",
                        "image_url": "data:image/png;base64,"
                        + base64.b64encode(image).decode("ascii"),
                    },
                ],
            }
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "receipt_extraction_v1",
                "strict": True,
                "schema": extraction_schema(config.provider) if schema is None else schema,
            }
        },
    }


@dataclass(frozen=True)
class Answer:
    text: str
    response: dict[str, Any]


class Provider(Protocol):
    def count(self, payload: dict[str, Any]) -> int: ...
    def extract(self, payload: dict[str, Any], max_output: int) -> Answer: ...
    def close(self) -> None: ...


class OpenAIProvider:
    def __init__(self) -> None:
        key = api_key("OPENAI_API_KEY")
        try:
            from openai import OpenAI
        except ImportError as error:
            raise RuntimeError(
                "Install optional dependencies: uv sync --locked --extra llm"
            ) from error
        self.client = OpenAI(
            api_key=key,
            base_url="https://api.openai.com/v1",
            max_retries=0,
            timeout=60,
        )

    def count(self, payload: dict[str, Any]) -> int:
        count = self.client.responses.input_tokens.count(**payload).input_tokens
        if not isinstance(count, int) or isinstance(count, bool):
            raise ValueError("Invalid input-token count from provider")
        return count

    def extract(self, payload: dict[str, Any], max_output: int) -> Answer:
        response = self.client.responses.create(
            **payload, max_output_tokens=max_output, store=False
        )
        return Answer(response.output_text, response.model_dump(mode="json"))

    def close(self) -> None:
        self.client.close()


def plan(inputs: Path, config: LLMConfig) -> dict[str, Any]:
    images = sorted(inputs.glob("*.png"))
    if not images:
        raise ValueError("No PNG images found")
    if len(images) > config.max_requests:
        raise ValueError(
            "Image count exceeds max_requests; select inputs or revise the explicit limit"
        )
    records = []
    for image in images:
        if image.stat().st_size > 20 * 1024 * 1024:
            raise ValueError("Input exceeds the local 20 MiB image limit")
        with Image.open(image) as decoded:
            if decoded.format != "PNG":
                raise ValueError("Expected PNG input")
            decoded.verify()
        records.append({"id": image.stem, "image_sha256": sha256(image)})
    prompt_text = prompt()
    schema = extraction_schema(config.provider)
    return {
        "mode": "offline-plan",
        "prompt": prompt_text,
        "output_schema": schema,
        "config": config.model_dump(),
        "documents": records,
        "prompt_sha256": hashlib.sha256(prompt_text.encode()).hexdigest(),
        "schema_sha256": hashlib.sha256(json.dumps(schema, sort_keys=True).encode()).hexdigest(),
        "paid_calls_made": 0,
        "estimated_cost_usd": None,
        "note": "Cost requires provider input-token counting; this plan does not contact the API",
    }


def decode(answer: Answer, document_id: str) -> RawReceipt:
    response = answer.response
    if response.get("status") != "completed":
        raise ValueError("IncompleteResponse")
    if any(
        part.get("type") == "refusal"
        for item in response.get("output", [])
        for part in item.get("content", [])
    ):
        raise ValueError("ModelRefusal")
    data = json.loads(answer.text)
    if not isinstance(data, dict) or "document_id" in data:
        raise ValueError("InvalidExtractionContract")
    raw = RawReceipt.model_validate({**data, "document_id": document_id})
    return raw.model_copy(update={"items_complete": False})


def run(
    inputs: Path, output: Path, config: LLMConfig, provider: Provider | None = None
) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError(f"Output already exists: {output}")
    prepared = plan(inputs, config)
    initialized = time.perf_counter()
    if provider is not None:
        engine = provider
    elif config.provider == "gemini-free":
        from receipttrace.gemini import GeminiProvider

        engine = GeminiProvider(config)
    else:
        engine = OpenAIProvider()
    initialization = time.perf_counter() - initialized
    try:
        output.mkdir(parents=True)
    except OSError:
        engine.close()
        raise
    records: list[dict[str, Any]] = []
    reserved = Decimal(0)
    measured = Decimal(0)
    unknown_usage = 0
    halted = False
    try:
        for index, document in enumerate(prepared["documents"]):
            if index and config.min_interval_seconds and not halted:
                time.sleep(config.min_interval_seconds)
            started = time.perf_counter()
            record: dict[str, Any] = {
                "id": document["id"],
                "image_sha256": document["image_sha256"],
            }
            sent = False
            usage_known = False
            try:
                if halted:
                    raise ValueError("StoppedAfterProviderHalt")
                image = (inputs / (document["id"] + ".png")).read_bytes()
                if hashlib.sha256(image).hexdigest() != document["image_sha256"]:
                    raise ValueError("InputChangedAfterPlan")
                payload = request(
                    image, config, prompt_text=prepared["prompt"], schema=prepared["output_schema"]
                )
                count = engine.count(payload)
                if type(count) is not int or not 0 <= count <= config.max_input_tokens:
                    raise ValueError("InputTokenLimit")
                reserve = config.estimate(count, config.max_output_tokens)
                record.update({"counted_input_tokens": count, "reserved_usd": str(reserve)})
                with localcontext() as arithmetic:
                    arithmetic.prec = 80
                    proposed_reservation = reserved + reserve
                if proposed_reservation > Decimal(config.max_budget_usd):
                    raise ValueError("BudgetReservationExceeded")
                reserved = proposed_reservation
                sent = True
                answer = engine.extract(payload, config.max_output_tokens)
                record["response"] = answer.response
                usage = answer.response.get("usage")
                if (
                    isinstance(usage, dict)
                    and type(usage.get("input_tokens")) is int
                    and type(usage.get("output_tokens")) is int
                ):
                    cost = config.estimate(usage["input_tokens"], usage["output_tokens"])
                    record["estimated_cost_usd"] = str(cost)
                    with localcontext() as arithmetic:
                        arithmetic.prec = 80
                        measured += cost
                    usage_known = True
                    if cost > reserve:
                        halted = True
                        raise ValueError("UsageExceededReservation")
                else:
                    raise ValueError("MissingUsage")
                raw = decode(answer, document["id"])
                record.update(
                    {"status": "ok", "validation": report(raw, "idr-grouped", Decimal(0))}
                )
            except Exception as error:
                # Never persist provider exception bodies: they may contain input or credentials.
                known = {
                    "IncompleteResponse",
                    "ModelRefusal",
                    "BudgetReservationExceeded",
                    "InputTokenLimit",
                    "InputChangedAfterPlan",
                    "UsageExceededReservation",
                    "MissingUsage",
                    "StoppedAfterProviderHalt",
                    "InvalidExtractionContract",
                }
                reason = (
                    str(error)
                    if type(error) is ValueError and str(error) in known
                    else type(error).__name__
                )
                record.update({"status": "error", "error_type": reason})
                if type(error).__name__ in {
                    "GeminiQuotaExceeded",
                    "GeminiFreeTierUnavailable",
                    "GeminiModelUnavailable",
                    "GeminiSchemaTooComplex",
                }:
                    halted = True
                if sent and not usage_known:
                    unknown_usage += 1
                    halted = True
            record["seconds"] = time.perf_counter() - started
            path = output / (document["id"] + ".json")
            path.write_text(
                json.dumps(record, ensure_ascii=False, indent=2, default=decimal_json) + "\n",
                encoding="utf-8",
            )
            records.append(
                {
                    "id": document["id"],
                    "file": path.name,
                    "sha256": sha256(path),
                    "status": record["status"],
                    "seconds": record["seconds"],
                }
            )
            print(
                f"{document['id']}: {record['status']}"
                + (f" ({record['error_type']})" if record["status"] == "error" else ""),
                flush=True,
            )
    finally:
        engine.close()
    git = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
    dirty = subprocess.run(
        ["git", "status", "--porcelain"], capture_output=True, text=True, check=False
    )
    manifest = {
        "schema_version": 1,
        "rules_version": "llm-extraction-1",
        "plan": prepared,
        "engine": {
            "provider": config.provider,
            "requested_model": config.model,
            "sdk": (version("httpx") if config.provider == "gemini-free" else version("openai"))
            if provider is None
            else "injected-test-provider",
            "store": False,
            "api": "interactions-v1beta" if config.provider == "gemini-free" else "responses",
            "thinking_level": config.thinking_level if config.provider == "gemini-free" else None,
            "counting_scope": "countTokens preflight; actual usage from Interactions"
            if config.provider == "gemini-free"
            else "Responses input token counting",
            "max_retries": 0,
            "image_detail": "high" if config.provider == "openai" else "provider-default",
        },
        "created_at_utc": datetime.now(UTC).isoformat(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "initialization_seconds": initialization,
        "latency_scope": "image + token-count API + inference + validation; excludes output IO",
        "git_commit": git.stdout.strip() if git.returncode == 0 else None,
        "git_dirty": bool(dirty.stdout) if dirty.returncode == 0 else None,
        "source_hashes": {str(path): sha256(path) for path in sorted(Path("src").rglob("*.py"))},
        "lock_sha256": sha256(Path("uv.lock")),
        "records": records,
        "cost_summary": {
            "currency": "USD",
            "reserved_usd": str(reserved),
            "estimated_known_usage_usd": str(measured),
            "requests_with_unknown_usage": unknown_usage,
            "not_an_invoice": True,
            "free_tier_condition": "User-confirmed Free Tier without billing; not verified by API"
            if config.provider == "gemini-free"
            else None,
            "config": config.model_dump(),
        },
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
