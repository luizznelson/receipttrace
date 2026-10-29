"""Explicit model, pricing and bounded run configuration. No price assumptions."""

from datetime import date
from decimal import Decimal, InvalidOperation, localcontext
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from receipttrace.domain import RawReceipt


class LLMConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    provider: Literal["openai", "gemini-free"] = "openai"
    thinking_level: Literal["minimal", "low", "medium", "high"] = "low"
    free_tier_confirmed: bool = False
    min_interval_seconds: int = Field(default=0, ge=0, le=120)
    model: str = Field(min_length=1, max_length=200)
    max_requests: int = Field(ge=1, le=100)
    max_output_tokens: int = Field(ge=256, le=4096)
    max_input_tokens: int = Field(ge=1, le=100_000)
    max_budget_usd: str
    input_usd_per_million: str
    output_usd_per_million: str
    pricing_as_of: str

    @field_validator("model")
    @classmethod
    def explicit_model(cls, value: str) -> str:
        if not value.strip() or value.startswith("SET_"):
            raise ValueError("Select an available vision model, preferably an immutable snapshot")
        return value

    @field_validator("max_budget_usd", "input_usd_per_million", "output_usd_per_million")
    @classmethod
    def positive_decimal(cls, value: str) -> str:
        try:
            number = Decimal(value)
        except InvalidOperation as error:
            raise ValueError("Expected a decimal string") from error
        if not number.is_finite() or number < 0 or len(value) > 32:
            raise ValueError("Expected a finite nonnegative decimal string")
        return value

    @field_validator("pricing_as_of")
    @classmethod
    def dated_pricing(cls, value: str) -> str:
        date.fromisoformat(value)
        return value

    @model_validator(mode="after")
    def provider_pricing(self) -> Self:
        amounts = (self.max_budget_usd, self.input_usd_per_million, self.output_usd_per_million)
        if self.provider == "gemini-free":
            if self.model not in {"gemini-2.5-flash", "gemini-3.8-flash", "gemini-3.5-flash-lite"}:
                raise ValueError("Model not in the verified Gemini free-tier allowlist")
            if self.model == "gemini-3.8-flash" and self.thinking_level == "minimal":
                raise ValueError("Gemini 3.8 Flash requires low, medium or high thinking")
            if any(Decimal(value) != 0 for value in amounts):
                raise ValueError("Gemini free-tier configuration must use zero prices and budget")
        elif any(Decimal(value) <= 0 for value in amounts):
            raise ValueError("OpenAI requires positive budget and prices")
        return self

    def estimate(self, input_tokens: int, output_tokens: int) -> Decimal:
        if input_tokens < 0 or output_tokens < 0:
            raise ValueError("Token counts must be nonnegative")
        with localcontext() as arithmetic:
            arithmetic.prec = 80
            return (
                Decimal(input_tokens) * Decimal(self.input_usd_per_million)
                + Decimal(output_tokens) * Decimal(self.output_usd_per_million)
            ) / Decimal(1_000_000)


def extraction_schema(provider: str = "openai") -> dict[str, Any]:
    schema = RawReceipt.model_json_schema()
    del schema["properties"]["document_id"]

    def strict(node: Any) -> None:
        if isinstance(node, dict):
            node.pop("default", None)
            if node.get("type") == "object":
                node["additionalProperties"] = False
                node["required"] = list(node["properties"])
            for value in node.values():
                strict(value)
        elif isinstance(node, list):
            for value in node:
                strict(value)

    strict(schema)
    if provider == "gemini-free":
        # Gemini only unrolls cyclic references through non-required properties.
        schema["$defs"]["RawItem"]["required"].remove("children")

        def simplify_transport(node: Any) -> None:
            if isinstance(node, dict):
                # Large nested array bounds explode the provider's constrained decoder states.
                # RawReceipt retains these limits when validating the returned JSON locally.
                node.pop("maxItems", None)
                node.pop("minItems", None)
                for value in node.values():
                    simplify_transport(value)
            elif isinstance(node, list):
                for value in node:
                    simplify_transport(value)

        simplify_transport(schema)
    return schema
