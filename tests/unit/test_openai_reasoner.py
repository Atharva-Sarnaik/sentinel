"""
tests.unit.test_openai_reasoner
===============================
Unit tests for the OpenAI Reasoner integration with structured outputs,
deterministic fallback, grounding guardrails, and audit metadata.

Owner:   SENTINEL Mission Control
Tier:    3 (Phase 4: OpenAI Reasoner Integration)
"""

from __future__ import annotations

import os
import uuid
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from libs.common.helpers import utc_now
from libs.contracts import (
    AuditEntry,
    Explanation,
    FusionDecision,
    Severity,
    SpecialistOpinion,
    Subsystem,
    TelemetryWindow,
    VerifierResult,
    VerifierStatus,
)
from services.reasoner.reasoner import (
    DEFAULT_PROMPT_VERSION,
    generate_explanation,
    generate_explanation_with_metadata,
    openai_generate_explanation,
)
from services.reasoner.schemas import (
    ReasonerExecutionMetadata,
    ReasonerOutputSchema,
)
from services.verifier import check_grounding


@pytest.fixture
def sample_decision() -> FusionDecision:
    wid = uuid.uuid4()
    opinion = SpecialistOpinion(
        window_id=wid,
        subsystem=Subsystem.POWER,
        anomaly_score=0.88,
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


@pytest.fixture
def mock_openai_response():
    parsed_obj = ReasonerOutputSchema(
        summary="Critical electrical fault detected on solar array power bus channels P-1 and P-2. Voltage collapse exceeds emergency thresholds.",
        cited_channels=["P-1", "P-2"],
        cited_severity="critical",
        supporting_evidence=[
            "Specialist run-pwr-01 flagged anomaly score 0.88 exceeding 0.50 threshold.",
            "Responsible telemetry channels P-1 and P-2 exhibit correlated voltage drop.",
        ],
        recommendations=[
            "Switch main EPS bus to secondary solar array regulator.",
            "Shed non-essential thermal and scientific payloads immediately.",
        ],
    )
    mock_choice = MagicMock()
    mock_choice.message.parsed = parsed_obj

    mock_usage = MagicMock()
    mock_usage.prompt_tokens = 220
    mock_usage.completion_tokens = 85
    mock_usage.total_tokens = 305

    mock_completion = MagicMock()
    mock_completion.id = "chatcmpl-test-sentinel-12345"
    mock_completion.choices = [mock_choice]
    mock_completion.usage = mock_usage

    return mock_completion


def test_openai_structured_output_success(sample_decision: FusionDecision, mock_openai_response: Any) -> None:
    """Verify that when OpenAI client parses valid structured output, metadata and explanation are correct."""
    with patch("services.reasoner.reasoner.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.beta.chat.completions.parse.return_value = mock_openai_response

        explanation, metadata = generate_explanation_with_metadata(
            decision=sample_decision,
            api_key="test-key-mock",
            llm_model="gpt-4o-mini",
        )

        assert explanation.decision_id == sample_decision.decision_id
        assert explanation.cited_severity == Severity.CRITICAL
        assert explanation.cited_channels == ["P-1", "P-2"]
        assert "Critical electrical fault" in explanation.text
        assert explanation.llm_model == "gpt-4o-mini"

        assert metadata.provider == "openai"
        assert metadata.model == "gpt-4o-mini"
        assert metadata.is_fallback is False
        assert metadata.fallback_reason is None
        assert metadata.response_id == "chatcmpl-test-sentinel-12345"
        assert len(metadata.recommendations) == 2
        assert len(metadata.supporting_evidence) == 2
        assert metadata.token_usage.get("total_tokens") == 305

        # Verify grounding verifier accepts the generated explanation
        verifier_res = check_grounding(explanation, sample_decision)
        assert verifier_res.status == VerifierStatus.GROUNDED
        assert len(verifier_res.ungrounded_claims) == 0


def test_openai_grounding_guardrail_clamps_extraneous_channels(sample_decision: FusionDecision) -> None:
    """Verify that ungrounded channels returned by LLM are sanitized by reasoner guardrails."""
    ungrounded_parsed = ReasonerOutputSchema(
        summary="Anomalous event observed across channels.",
        cited_channels=["P-1", "GHOST-CHANNEL-999"],
        cited_severity="warning",  # Mismatched severity
        supporting_evidence=["Some evidence"],
        recommendations=["Action item"],
    )
    mock_completion = MagicMock()
    mock_completion.id = "chatcmpl-guardrail-test"
    mock_choice = MagicMock()
    mock_choice.message.parsed = ungrounded_parsed
    mock_completion.choices = [mock_choice]
    mock_completion.usage = MagicMock(prompt_tokens=100, completion_tokens=50, total_tokens=150)

    with patch("services.reasoner.reasoner.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.beta.chat.completions.parse.return_value = mock_completion

        explanation, metadata = generate_explanation_with_metadata(
            decision=sample_decision,
            api_key="test-key-mock",
            llm_model="gpt-4o-mini",
        )

        # Cited channels must NOT contain GHOST-CHANNEL-999
        assert "GHOST-CHANNEL-999" not in explanation.cited_channels
        assert explanation.cited_channels == ["P-1"]
        # Cited severity must match decision severity
        assert explanation.cited_severity == sample_decision.severity

        # Verifier must accept
        verifier_res = check_grounding(explanation, sample_decision)
        assert verifier_res.status == VerifierStatus.GROUNDED


def test_openai_timeout_triggers_mock_fallback(sample_decision: FusionDecision) -> None:
    """Verify that OpenAI timeout triggers graceful fallback to deterministic mock reasoner."""
    import openai

    with patch("services.reasoner.reasoner.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.beta.chat.completions.parse.side_effect = openai.APITimeoutError(request=MagicMock())

        explanation, metadata = generate_explanation_with_metadata(
            decision=sample_decision,
            api_key="test-key-mock",
            llm_model="gpt-4o-mini",
        )

        assert metadata.is_fallback is True
        assert metadata.provider == "mock-reasoner"
        assert metadata.fallback_reason is not None
        assert "timed out" in metadata.fallback_reason.lower()

        # Explanation is still valid and grounded
        assert explanation.decision_id == sample_decision.decision_id
        assert explanation.cited_severity == sample_decision.severity
        verifier_res = check_grounding(explanation, sample_decision)
        assert verifier_res.status == VerifierStatus.GROUNDED


def test_openai_authentication_error_triggers_fallback(sample_decision: FusionDecision) -> None:
    """Verify that OpenAI auth error triggers graceful fallback."""
    import openai

    with patch("services.reasoner.reasoner.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.beta.chat.completions.parse.side_effect = openai.AuthenticationError(
            message="Invalid API Key",
            response=MagicMock(status_code=401),
            body=None,
        )

        explanation, metadata = generate_explanation_with_metadata(
            decision=sample_decision,
            api_key="invalid-key",
            llm_model="gpt-4o-mini",
        )

        assert metadata.is_fallback is True
        assert metadata.provider == "mock-reasoner"
        assert "authentication" in metadata.fallback_reason.lower()

        verifier_res = check_grounding(explanation, sample_decision)
        assert verifier_res.status == VerifierStatus.GROUNDED


def test_openai_rate_limit_error_triggers_fallback(sample_decision: FusionDecision) -> None:
    """Verify that OpenAI rate limit triggers graceful fallback."""
    import openai

    with patch("services.reasoner.reasoner.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.beta.chat.completions.parse.side_effect = openai.RateLimitError(
            message="Rate limit exceeded",
            response=MagicMock(status_code=429),
            body=None,
        )

        explanation, metadata = generate_explanation_with_metadata(
            decision=sample_decision,
            api_key="test-key",
            llm_model="gpt-4o-mini",
        )

        assert metadata.is_fallback is True
        assert metadata.provider == "mock-reasoner"
        assert "rate limit" in metadata.fallback_reason.lower()

        verifier_res = check_grounding(explanation, sample_decision)
        assert verifier_res.status == VerifierStatus.GROUNDED


def test_missing_api_key_falls_back_to_mock(sample_decision: FusionDecision) -> None:
    """Verify that absence of OPENAI_API_KEY defaults cleanly to mock reasoner."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
        explanation, metadata = generate_explanation_with_metadata(
            decision=sample_decision,
            api_key="",
            llm_model="gpt-4o-mini",
        )

        assert metadata.is_fallback is True
        assert metadata.provider == "mock-reasoner"
        assert "not configured" in metadata.fallback_reason.lower()
        assert explanation.decision_id == sample_decision.decision_id
        verifier_res = check_grounding(explanation, sample_decision)
        assert verifier_res.status == VerifierStatus.GROUNDED


def test_generate_explanation_backward_compatibility(sample_decision: FusionDecision) -> None:
    """Verify that the original generate_explanation signature works unchanged."""
    explanation = generate_explanation(
        decision=sample_decision,
        prompt_version=DEFAULT_PROMPT_VERSION,
        llm_model="mock-reasoner",
    )
    assert isinstance(explanation, Explanation)
    assert explanation.decision_id == sample_decision.decision_id
    assert explanation.llm_model == "mock-reasoner"


def test_orchestrator_pipeline_captures_reasoner_metadata(sample_decision: FusionDecision) -> None:
    """Verify that the full LangGraph orchestrator pipeline records reasoner metadata in audit_entry.extra."""
    from services.orchestrator.graph import run_pipeline

    window = TelemetryWindow(
        window_id=sample_decision.window_id,
        subsystem=Subsystem.POWER,
        start_time=utc_now(),
        end_time=utc_now(),
        channels={"P-1": [1.2, 1.3, 1.4], "P-2": [0.8, 0.7, 0.6]},
        source_dataset="SMAP",
    )

    state = run_pipeline(window)

    assert "reasoner_metadata" in state
    meta = state["reasoner_metadata"]
    assert isinstance(meta, dict)
    assert "provider" in meta

    audit_entry = state["audit_entry"]
    assert "reasoner" in audit_entry.extra
    reasoner_extra = audit_entry.extra["reasoner"]
    assert "provider" in reasoner_extra
    assert "model" in reasoner_extra
    assert "is_fallback" in reasoner_extra
    assert "recommendations" in reasoner_extra
    assert "supporting_evidence" in reasoner_extra
