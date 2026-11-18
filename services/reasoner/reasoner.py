"""
services.reasoner.reasoner
============================
LLM Reasoner — produces grounded natural-language explanations and flight operations
guidance from FusionDecision evidence using OpenAI Structured Outputs (Phase 4).

Design rules (ADR-0002):
  • The LLM explains; it does NOT decide severity (fusion engine decides).
  • Output strictly adheres to ReasonerOutputSchema via OpenAI response parsing.
  • The verifier (services.verifier) checks every output for evidence grounding.
  • Fallback to deterministic mock reasoner on missing credentials, timeouts,
    rate limits, or API errors without corrupting pipeline execution.

Owner:   SENTINEL Core Team
Tier:    3 (Task T3.2 / Phase 4)
Status:  complete — production-ready OpenAI reasoner with robust fallback and audit telemetry.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from libs.common.helpers import utc_now
from libs.contracts import Explanation, FusionDecision, Severity
from services.reasoner.schemas import (
    EXPLANATION_JSON_SCHEMA,
    ReasonerExecutionMetadata,
    ReasonerOutputSchema,
)

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore[assignment, misc]

logger = logging.getLogger("sentinel.reasoner")

PROMPTS_DIR = Path("services/reasoner/prompts")
DEFAULT_PROMPT_VERSION = "v1.0.0"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_TIMEOUT_SECONDS = 15.0


def get_openai_config() -> dict[str, Any]:
    """
    Read OpenAI configuration safely from project-root .env and system environment.
    Credentials remain strictly backend-only.
    """
    # Load from root .env if present
    root_env = Path(".env")
    if root_env.is_file():
        load_dotenv(dotenv_path=root_env, override=False)

    api_key = os.getenv("OPENAI_API_KEY", "").strip() or None
    model = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL).strip()
    timeout = float(os.getenv("OPENAI_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS)))
    temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.0"))
    max_retries = int(os.getenv("OPENAI_MAX_RETRIES", "2"))

    return {
        "api_key": api_key,
        "model": model,
        "timeout": timeout,
        "temperature": temperature,
        "max_retries": max_retries,
    }


def load_prompt_template(version: str = DEFAULT_PROMPT_VERSION) -> str:
    """
    Load a versioned prompt template from disk with fallback to explain.txt.
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
    Deterministic grounded mock generator for offline CI, testing, and fallback.
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


def openai_generate_explanation(
    decision: FusionDecision,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
    llm_model: str = DEFAULT_OPENAI_MODEL,
    api_key: str | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    temperature: float = 0.0,
    max_retries: int = 2,
) -> tuple[Explanation, ReasonerExecutionMetadata]:
    """
    Invoke OpenAI with structured outputs enforcing strict evidence grounding.
    """
    if OpenAI is None:
        raise RuntimeError("OpenAI SDK is not installed or available.")

    start_time = time.perf_counter()
    client = OpenAI(
        api_key=api_key,
        timeout=timeout,
        max_retries=max_retries,
    )

    template = load_prompt_template(prompt_version)
    evidence = decision.evidence_summary()
    evidence_json = json.dumps(evidence, indent=2)

    prompt_content = (
        template.replace("{{FUSION_DECISION_JSON}}", evidence_json)
        .replace("{{EVIDENCE_JSON}}", evidence_json)
        .replace("{{FUSED_SEVERITY}}", decision.severity.value)
    )

    system_instruction = (
        "You are SENTINEL's Satellite Telemetry Health & Anomaly Reasoner. "
        "Strictly adhere to the provided evidence. You must cite ONLY responsible channels "
        f"and cited_severity must strictly match '{decision.severity.value}'. "
        "Provide factual supporting evidence and actionable operational recommendations."
    )

    completion = client.beta.chat.completions.parse(
        model=llm_model,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt_content},
        ],
        response_format=ReasonerOutputSchema,
        temperature=temperature,
    )

    latency_ms = (time.perf_counter() - start_time) * 1000.0
    parsed: ReasonerOutputSchema = completion.choices[0].message.parsed  # type: ignore[assignment]
    if parsed is None:
        raise ValueError("OpenAI structured output parsing returned None.")

    # Guardrail: strict grounding enforcement on severity and channels
    severity_val = parsed.cited_severity.lower().strip()
    try:
        parsed_sev = Severity(severity_val)
    except ValueError:
        parsed_sev = decision.severity

    # Grounding guardrail: cited severity MUST strictly match fused decision severity
    cited_sev = decision.severity if parsed_sev != decision.severity else parsed_sev

    # Enforce evidence grounding: channels must be in responsible_channels
    allowed_channels: set[str] = set()
    for op in decision.opinions:
        allowed_channels.update(op.responsible_channels)
    grounded_channels = [ch for ch in parsed.cited_channels if ch in allowed_channels]

    # Format composite explanation text
    text_blocks = [parsed.summary]
    if parsed.supporting_evidence:
        text_blocks.append("\nSupporting Evidence:\n" + "\n".join(f"• {e}" for e in parsed.supporting_evidence))
    if parsed.recommendations:
        text_blocks.append("\nOperational Recommendations:\n" + "\n".join(f"→ {r}" for r in parsed.recommendations))

    composite_text = "\n".join(text_blocks)

    explanation = Explanation(
        decision_id=decision.decision_id,
        text=composite_text,
        cited_channels=grounded_channels,
        cited_severity=cited_sev,
        prompt_version=prompt_version,
        llm_model=llm_model,
        created_at=utc_now(),
    )

    token_usage = {
        "input_tokens": completion.usage.prompt_tokens if completion.usage else 0,
        "output_tokens": completion.usage.completion_tokens if completion.usage else 0,
        "total_tokens": completion.usage.total_tokens if completion.usage else 0,
    }

    metadata = ReasonerExecutionMetadata(
        provider="openai",
        model=llm_model,
        prompt_version=prompt_version,
        response_id=completion.id,
        latency_ms=round(latency_ms, 2),
        token_usage=token_usage,
        is_fallback=False,
        fallback_reason=None,
        summary=parsed.summary,
        supporting_evidence=parsed.supporting_evidence,
        recommendations=parsed.recommendations,
    )

    return explanation, metadata


def generate_explanation_with_metadata(
    decision: FusionDecision,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
    llm_model: str | None = None,
    inject_hallucination: bool = False,
    api_key: str | None = None,
) -> tuple[Explanation, ReasonerExecutionMetadata]:
    """
    Primary reasoner entry point returning both the validated Explanation contract
    and comprehensive execution metadata.
    """
    config = get_openai_config()
    active_key = api_key or config["api_key"]
    model_name = llm_model or config["model"]

    # Explicit offline mock requested
    if model_name == "mock-reasoner" or inject_hallucination:
        start_time = time.perf_counter()
        expl = mock_generate_explanation(
            decision=decision,
            prompt_version=prompt_version,
            llm_model="mock-reasoner",
            inject_hallucination=inject_hallucination,
        )
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        meta = ReasonerExecutionMetadata(
            provider="mock",
            model="mock-reasoner",
            prompt_version=prompt_version,
            response_id=None,
            latency_ms=round(latency_ms, 2),
            token_usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            is_fallback=False,
            fallback_reason=None,
            summary=expl.text,
            supporting_evidence=[
                f"Specialist '{op.subsystem.value}' anomaly score: {op.anomaly_score:.2f} (threshold: {op.threshold_used:.2f})"
                for op in decision.opinions
            ],
            recommendations=[
                "Maintain standard telemetry monitoring corridor."
                if decision.severity == Severity.NOMINAL
                else f"Review telemetry parameters for subsystem '{decision.attributed_subsystem.value if decision.attributed_subsystem else 'active'}'."
            ],
        )
        return expl, meta

    # If no API key configured, cleanly activate deterministic fallback
    if not active_key:
        logger.info("OPENAI_API_KEY not configured. Falling back to deterministic reasoner.")
        start_time = time.perf_counter()
        expl = mock_generate_explanation(
            decision=decision,
            prompt_version=prompt_version,
            llm_model=f"{model_name}-fallback",
            inject_hallucination=False,
        )
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        meta = ReasonerExecutionMetadata(
            provider="mock-reasoner",
            model=f"{model_name}-fallback",
            prompt_version=prompt_version,
            response_id=None,
            latency_ms=round(latency_ms, 2),
            token_usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            is_fallback=True,
            fallback_reason="OPENAI_API_KEY not configured in .env",
            summary=expl.text,
            supporting_evidence=[
                f"Specialist '{op.subsystem.value}' score {op.anomaly_score:.2f} under rule '{decision.fusion_rule_applied}'"
                for op in decision.opinions
            ],
            recommendations=[
                "Continue automated corridor monitoring."
                if decision.severity == Severity.NOMINAL
                else f"Execute containment procedures for {decision.attributed_subsystem.value if decision.attributed_subsystem else 'system'}."
            ],
        )
        return expl, meta

    # Live OpenAI API invocation with structured exception handling
    try:
        return openai_generate_explanation(
            decision=decision,
            prompt_version=prompt_version,
            llm_model=model_name,
            api_key=active_key,
            timeout=config["timeout"],
            temperature=config["temperature"],
            max_retries=config["max_retries"],
        )
    except Exception as e:
        logger.warning(
            f"OpenAI reasoner call failed ({type(e).__name__}: {e}). Engaging deterministic fallback."
        )
        start_time = time.perf_counter()
        expl = mock_generate_explanation(
            decision=decision,
            prompt_version=prompt_version,
            llm_model=f"{model_name}-fallback",
            inject_hallucination=False,
        )
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        meta = ReasonerExecutionMetadata(
            provider="mock-reasoner",
            model=f"{model_name}-fallback",
            prompt_version=prompt_version,
            response_id=None,
            latency_ms=round(latency_ms, 2),
            token_usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            is_fallback=True,
            fallback_reason=f"{type(e).__name__}: {e}",
            summary=expl.text,
            supporting_evidence=[
                f"Subsystem '{op.subsystem.value}' evaluated at score {op.anomaly_score:.2f}"
                for op in decision.opinions
            ],
            recommendations=[
                "Maintain baseline telemetry reception."
                if decision.severity == Severity.NOMINAL
                else f"Verify backup operational limits for {decision.attributed_subsystem.value if decision.attributed_subsystem else 'spacecraft'}."
            ],
        )
        return expl, meta


def generate_explanation(
    decision: FusionDecision,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
    llm_model: str | None = None,
    inject_hallucination: bool = False,
    api_key: str | None = None,
) -> Explanation:
    """
    Standard reasoner entry point returning the validated Explanation contract.
    Maintains 100% backward compatibility with all pipeline callers and test suites.
    """
    explanation, _ = generate_explanation_with_metadata(
        decision=decision,
        prompt_version=prompt_version,
        llm_model=llm_model,
        inject_hallucination=inject_hallucination,
        api_key=api_key,
    )
    return explanation
