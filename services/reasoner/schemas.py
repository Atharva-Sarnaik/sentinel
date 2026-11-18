"""
services.reasoner.schemas
===========================
Pydantic schemas and JSON schema definitions for the Sentinel LLM Reasoner (Phase 4).

Features:
  • ReasonerOutputSchema: Pydantic model for strict OpenAI structured output enforcement.
  • ReasonerMetadata: Execution telemetry including provider, model, token usage, latency, and fallback state.
  • EXPLANATION_JSON_SCHEMA: Backward-compatible JSON schema for offline validation.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Strict Pydantic Schema for OpenAI Structured Outputs
# ---------------------------------------------------------------------------


class ReasonerOutputSchema(BaseModel):
    """
    Structured Pydantic response schema enforced on OpenAI API calls.

    Strict Grounding Rules (ADR-0002):
      • cited_severity: must strictly match FusionDecision.severity.
      • cited_channels: must only contain responsible channels from the evidence (empty if nominal).
      • summary: concise, factual natural-language summary.
      • supporting_evidence: verified bullet points from specialist findings.
      • recommendations: actionable flight operations guidance grounded in findings.
    """

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(
        ...,
        description="Concise, factual natural-language explanation of the spacecraft telemetry health or detected anomaly.",
    )
    cited_channels: list[str] = Field(
        default_factory=list,
        description="Exact channel IDs present in the evidence that triggered anomaly flags. Must be an empty list if health is nominal.",
    )
    cited_severity: str = Field(
        ...,
        description="Exact severity level cited from the evidence: 'nominal', 'advisory', 'warning', or 'critical'.",
    )
    supporting_evidence: list[str] = Field(
        default_factory=list,
        description="Verified factual bullet points citing specialist opinion scores, thresholds, and subsystem behaviors.",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Actionable flight controller recommendations grounded strictly in the observed telemetry state.",
    )


class ReasonerExecutionMetadata(BaseModel):
    """
    Execution telemetry captured for every reasoner invocation for SQLite audit and observability.
    """

    provider: str = Field(default="openai", description="Reasoner provider: 'openai' or 'mock'")
    model: str = Field(default="gpt-4o-mini", description="LLM model identifier used")
    prompt_version: str = Field(default="v1.0.0", description="Version of the prompt template applied")
    response_id: str | None = Field(default=None, description="OpenAI API response / completion ID")
    latency_ms: float = Field(default=0.0, description="End-to-end LLM inference latency in milliseconds")
    token_usage: dict[str, int] = Field(
        default_factory=lambda: {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
        description="Token consumption metrics",
    )
    is_fallback: bool = Field(default=False, description="True if fallback reasoning was invoked")
    fallback_reason: str | None = Field(default=None, description="Diagnostic error message if fallback occurred")
    summary: str = Field(default="", description="Core reasoner summary")
    supporting_evidence: list[str] = Field(default_factory=list, description="Grounding evidence points")
    recommendations: list[str] = Field(default_factory=list, description="Operational recommendations")


# ---------------------------------------------------------------------------
# Backward-compatible JSON Schema
# ---------------------------------------------------------------------------

EXPLANATION_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "ExplanationOutput",
    "description": (
        "Structured output from the Sentinel LLM reasoner. "
        "The LLM must cite only channels and severity present in the evidence."
    ),
    "type": "object",
    "required": ["text", "cited_channels", "cited_severity"],
    "additionalProperties": False,
    "properties": {
        "text": {
            "type": "string",
            "description": "Natural-language explanation of the anomaly.",
        },
        "cited_channels": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Channel names referenced in the explanation.",
        },
        "cited_severity": {
            "type": "string",
            "enum": ["nominal", "advisory", "warning", "critical"],
            "description": "Severity cited in the explanation — must match FusionDecision.severity.",
        },
    },
}
