"""
services.reasoner.schemas
===========================
JSON schema for the LLM reasoner output.

The schema is enforced at the API boundary and again by the verifier.
Prompts must instruct the LLM to produce output matching this schema.

Owner:   Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    3 (task T3.2)
Status:  not started
"""

from __future__ import annotations

# JSON Schema definition for LLM structured output.
# This will be used in the system prompt and for validation.
EXPLANATION_JSON_SCHEMA: dict = {
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
