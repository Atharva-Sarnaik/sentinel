"""
tests.unit.test_reasoner
========================
Unit tests for the LLM reasoner, JSON schema validation, and versioned prompts (task T3.2).

Owner:   Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    3 (task T3.2)
Status:  complete — validates schema compliance, grounded mock reasoning, and prompt loading.
"""

from __future__ import annotations

import uuid

import pytest
from jsonschema import ValidationError, validate

from libs.common.helpers import utc_now
from libs.contracts import FusionDecision, Severity, SpecialistOpinion, Subsystem
from services.reasoner.reasoner import (
    DEFAULT_PROMPT_VERSION,
    generate_explanation,
    load_prompt_template,
)
from services.reasoner.schemas import EXPLANATION_JSON_SCHEMA


@pytest.fixture
def sample_decision() -> FusionDecision:
    wid = uuid.uuid4()
    opinion = SpecialistOpinion(
        window_id=wid,
        subsystem=Subsystem.POWER,
        anomaly_score=0.85,
        severity=Severity.CRITICAL,
        responsible_channels=["P-1", "P-2"],
        threshold_used=0.5,
        model_run_id="run-pwr-01",
        created_at=utc_now(),
    )
    return FusionDecision(
        window_id=wid,
        opinions=[opinion],
        severity=Severity.CRITICAL,
        corroborating_subsystems=[Subsystem.POWER],
        attributed_subsystem=Subsystem.POWER,
        fusion_rule_applied="single_subsystem_isolated",
        created_at=utc_now(),
    )


def test_schema_validates_correct_payload() -> None:
    valid_payload = {
        "text": "Voltage spike on P-1 exceeded critical limits.",
        "cited_channels": ["P-1"],
        "cited_severity": "critical",
    }
    # Should not raise
    validate(instance=valid_payload, schema=EXPLANATION_JSON_SCHEMA)


def test_schema_rejects_missing_fields() -> None:
    invalid_payload = {
        "text": "Incomplete payload missing cited_severity.",
        "cited_channels": ["P-1"],
    }
    with pytest.raises(ValidationError):
        validate(instance=invalid_payload, schema=EXPLANATION_JSON_SCHEMA)


def test_schema_rejects_invalid_severity() -> None:
    invalid_payload = {
        "text": "Payload with non-standard severity.",
        "cited_channels": ["P-1"],
        "cited_severity": "catastrophic",
    }
    with pytest.raises(ValidationError):
        validate(instance=invalid_payload, schema=EXPLANATION_JSON_SCHEMA)


def test_load_prompt_template() -> None:
    template = load_prompt_template(DEFAULT_PROMPT_VERSION)
    assert len(template) > 20
    assert "EVIDENCE:" in template or "FusionDecision" in template


def test_mock_generate_explanation_grounded(sample_decision: FusionDecision) -> None:
    explanation = generate_explanation(
        decision=sample_decision,
        prompt_version=DEFAULT_PROMPT_VERSION,
        llm_model="mock-reasoner",
    )
    assert explanation.decision_id == sample_decision.decision_id
    assert explanation.cited_severity == sample_decision.severity
    assert set(explanation.cited_channels) == {"P-1", "P-2"}
    assert "P-1" in explanation.text
    assert explanation.llm_model == "mock-reasoner"


def test_mock_generate_explanation_hallucination_injection(sample_decision: FusionDecision) -> None:
    explanation = generate_explanation(
        decision=sample_decision,
        prompt_version=DEFAULT_PROMPT_VERSION,
        llm_model="mock-reasoner",
        inject_hallucination=True,
    )
    assert "UNGROUNDED_GHOST_CHANNEL_999" in explanation.cited_channels
    assert explanation.cited_severity != sample_decision.severity
