"""Explicit model, pricing and bounded run configuration. No price assumptions."""

from datetime import date
from decimal import Decimal, InvalidOperation, localcontext
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from receipttrace.domain import RawReceipt


class LLMConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

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
        if not number.is_finite() or number <= 0 or len(value) > 32:
            raise ValueError("Expected a finite positive decimal string")
        return value

    @field_validator("pricing_as_of")
    @classmethod
    def dated_pricing(cls, value: str) -> str:
        date.fromisoformat(value)
        return value

    def estimate(self, input_tokens: int, output_tokens: int) -> Decimal:
        if input_tokens < 0 or output_tokens < 0:
            raise ValueError("Token counts must be nonnegative")
        with localcontext() as arithmetic:
            arithmetic.prec = 80
            return (
                Decimal(input_tokens) * Decimal(self.input_usd_per_million)
                + Decimal(output_tokens) * Decimal(self.output_usd_per_million)
            ) / Decimal(1_000_000)


def extraction_schema() -> dict[str, Any]:
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
    return schema
