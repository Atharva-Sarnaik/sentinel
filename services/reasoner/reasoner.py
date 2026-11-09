"""
services.reasoner.reasoner
============================
LLM Reasoner — produces natural-language explanations from FusionDecision evidence.

Design rule (ADR-0002):
  • The LLM explains; it does NOT decide severity.
  • Prompts are versioned files in services/reasoner/prompts/.
  • Output must conform to the Explanation JSON schema.
  • The verifier (services.verifier) checks every output for grounding.

Owner:   Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    3 (task T3.2)
Status:  complete — versioned prompt runner with grounded mock fallback and JSON validation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from libs.common.helpers import utc_now
from libs.contracts import Explanation, FusionDecision, Severity
from services.reasoner.schemas import EXPLANATION_JSON_SCHEMA

PROMPTS_DIR = Path("services/reasoner/prompts")
DEFAULT_PROMPT_VERSION = "v1.0.0"


def load_prompt_template(version: str = DEFAULT_PROMPT_VERSION) -> str:
    """
    Load a versioned prompt template from disk.
    Falls back to explain.txt if a specific versioned file is not found.
    """
    version_file = PROMPTS_DIR / f"explain_{version}.txt"
    if version_file.is_file():
        return version_file.read_text(encoding="utf-8")

    default_file = PROMPTS_DIR / "explain.txt"
    if default_file.is_file():
        return default_file.read_text(encoding="utf-8")

    return (
        "You are Sentinel telemetry health analyst.\n"
        "Explain the detected anomaly using only the evidence provided.\n"
        "EVIDENCE: {{FUSION_DECISION_JSON}}\n"
    )


def mock_generate_explanation(
    decision: FusionDecision,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
    llm_model: str = "mock-reasoner",
    inject_hallucination: bool = False,
) -> Explanation:
    """
    Deterministic grounded mock generator for offline CI and testing.
    Produces valid Explanation contracts without making external API calls.
    """
    # Collect cited channels from evidence
    cited_channels: list[str] = []
    for op in decision.opinions:
        cited_channels.extend(op.responsible_channels)

    # Deduplicate while preserving order
    cited_channels = list(dict.fromkeys(cited_channels))

    cited_severity = decision.severity

    if inject_hallucination:
        # Deliberately cite an ungrounded channel and wrong severity for testing verifier
        cited_channels.append("UNGROUNDED_GHOST_CHANNEL_999")
        cited_severity = (
            Severity.CRITICAL if decision.severity != Severity.CRITICAL else Severity.NOMINAL
        )
        text = (
            f"[HALLUCINATED] Anomaly detected on channel {cited_channels[-1]} "
            f"with severity {cited_severity.value}."
        )
    elif not decision.is_anomalous:
        text = (
            f"Spacecraft telemetry health is nominal. All {len(decision.opinions)} "
            f"subsystems are operating within established tolerance thresholds under "
            f"rule '{decision.fusion_rule_applied}'."
        )
    else:
        channels_str = ", ".join(cited_channels) if cited_channels else "system-level indicators"
        attrib_str = (
            f"Subsystem '{decision.attributed_subsystem.value}'"
            if decision.attributed_subsystem
            else "Satellite fleet"
        )
        text = (
            f"{attrib_str} flagged an anomaly with severity {decision.severity.value}. "
            f"Telemetry evidence observed on channel(s): {channels_str}. "
            f"Fusion rule '{decision.fusion_rule_applied}' applied."
        )

    # Verify that mock output adheres to the JSON schema
    payload: dict[str, Any] = {
        "text": text,
        "cited_channels": cited_channels,
        "cited_severity": cited_severity.value,
    }
    validate(instance=payload, schema=EXPLANATION_JSON_SCHEMA)

    return Explanation(
        decision_id=decision.decision_id,
        text=text,
        cited_channels=cited_channels,
        cited_severity=cited_severity,
        prompt_version=prompt_version,
        llm_model=llm_model,
        created_at=utc_now(),
    )


def generate_explanation(
    decision: FusionDecision,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
    llm_model: str = "mock-reasoner",
    inject_hallucination: bool = False,
    api_key: str | None = None,
) -> Explanation:
    """
    Call the LLM with a versioned prompt to explain a FusionDecision.

    Args:
        decision: The FusionDecision produced by the fusion engine.
        prompt_version: Version identifier of the prompt template to use.
        llm_model: LLM model identifier (e.g. 'gpt-4o-mini' or 'mock-reasoner').
        inject_hallucination: Flag to trigger intentional ungrounded claims (for verifier testing).
        api_key: Optional API key for live LLM providers.

    Returns:
        An Explanation with structured citations for verifier grounding.
    """
    # If using mock-reasoner or no API key, use deterministic mock
    if llm_model == "mock-reasoner" or not api_key:
        return mock_generate_explanation(
            decision=decision,
            prompt_version=prompt_version,
            llm_model=llm_model,
            inject_hallucination=inject_hallucination,
        )

    # Live LLM provider path (OpenAI)
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        template = load_prompt_template(prompt_version)
        evidence_json = json.dumps(decision.evidence_summary(), indent=2)
        prompt_content = template.replace("{{FUSION_DECISION_JSON}}", evidence_json)

        response = client.chat.completions.create(
            model=llm_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a telemetry health assistant. Respond strictly with JSON.",
                },
                {"role": "user", "content": prompt_content},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=512,
        )

        content = response.choices[0].message.content or "{}"
        data = json.loads(content)
        validate(instance=data, schema=EXPLANATION_JSON_SCHEMA)

        return Explanation(
            decision_id=decision.decision_id,
            text=data["text"],
            cited_channels=data.get("cited_channels", []),
            cited_severity=Severity(data["cited_severity"].lower()),
            prompt_version=prompt_version,
            llm_model=llm_model,
            created_at=utc_now(),
        )
    except (ValidationError, Exception):
        # Fall back to deterministic mock if live call fails or output is malformed
        return mock_generate_explanation(
            decision=decision,
            prompt_version=prompt_version,
            llm_model=f"{llm_model}-fallback",
            inject_hallucination=False,
        )
