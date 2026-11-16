"""
tests.unit.test_verifier
========================
Unit tests for the grounding verifier and retry policy (tasks T3.3 & T3.4).

Verifies ADR-0002 compliance:
  • Rejects ungrounded channel citations and severity mismatches.
  • Enforces max 2 retries (total 3 attempts).
  • Implements clean abstention path (evidence-only report on failure).

Owner:   Sujal Hede (@Sujalhede) / Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    3 (tasks T3.3 & T3.4)
Status:  complete — validates grounding check, retry policy, and abstention fallback.
"""

from __future__ import annotations

import uuid

import pytest

from libs.common.helpers import utc_now
from libs.contracts import (
    Explanation,
    FusionDecision,
    Severity,
    SpecialistOpinion,
    Subsystem,
    VerifierStatus,
)
from services.verifier.grounding import check_grounding
from services.verifier.retry import MAX_RETRIES, verify_with_retry


@pytest.fixture
def grounded_decision_and_explanation() -> tuple[FusionDecision, Explanation]:
    wid = uuid.uuid4()
    did = uuid.uuid4()
    opinion = SpecialistOpinion(
        window_id=wid,
        subsystem=Subsystem.POWER,
        anomaly_score=0.75,
        severity=Severity.WARNING,
        responsible_channels=["P-1"],
        threshold_used=0.5,
        model_run_id="run-pwr-01",
        created_at=utc_now(),
    )
    decision = FusionDecision(
        decision_id=did,
        window_id=wid,
        opinions=[opinion],
        severity=Severity.WARNING,
        corroborating_subsystems=[Subsystem.POWER],
        attributed_subsystem=Subsystem.POWER,
        fusion_rule_applied="single_subsystem_isolated",
        created_at=utc_now(),
    )
    explanation = Explanation(
        decision_id=did,
        text="Telemetry indicates a power warning on channel P-1.",
        cited_channels=["P-1"],
        cited_severity=Severity.WARNING,
        prompt_version="v1.0.0",
        llm_model="mock-reasoner",
        created_at=utc_now(),
    )
    return decision, explanation


def test_grounding_passes_on_valid_evidence(
    grounded_decision_and_explanation: tuple[FusionDecision, Explanation],
) -> None:
    decision, explanation = grounded_decision_and_explanation
    result = check_grounding(explanation, decision)

    assert result.is_grounded is True
    assert result.status == VerifierStatus.GROUNDED
    assert len(result.ungrounded_claims) == 0


def test_grounding_fails_on_severity_mismatch(
    grounded_decision_and_explanation: tuple[FusionDecision, Explanation],
) -> None:
    decision, explanation = grounded_decision_and_explanation
    # Escalate severity without evidence
    faulty_explanation = Explanation(
        decision_id=decision.decision_id,
        text="Critical failure on channel P-1.",
        cited_channels=["P-1"],
        cited_severity=Severity.CRITICAL,  # Evidence says WARNING
        prompt_version="v1.0.0",
        llm_model="mock-reasoner",
        created_at=utc_now(),
    )

    result = check_grounding(faulty_explanation, decision)
    assert result.is_grounded is False
    assert result.status == VerifierStatus.UNGROUNDED
    assert any("Severity mismatch" in claim for claim in result.ungrounded_claims)


def test_grounding_fails_on_hallucinated_channel(
    grounded_decision_and_explanation: tuple[FusionDecision, Explanation],
) -> None:
    decision, explanation = grounded_decision_and_explanation
    # Cite phantom channel not in evidence
    faulty_explanation = Explanation(
        decision_id=decision.decision_id,
        text="Thermal runaway on channel T-999 and P-1.",
        cited_channels=["P-1", "T-999"],  # T-999 is hallucinated
        cited_severity=Severity.WARNING,
        prompt_version="v1.0.0",
        llm_model="mock-reasoner",
        created_at=utc_now(),
    )

    result = check_grounding(faulty_explanation, decision)
    assert result.is_grounded is False
    assert any("T-999" in claim for claim in result.ungrounded_claims)


def test_verify_with_retry_succeeds_first_attempt(
    grounded_decision_and_explanation: tuple[FusionDecision, Explanation],
) -> None:
    decision, explanation = grounded_decision_and_explanation

    exp, ver_res = verify_with_retry(
        decision=decision,
        generate_fn=lambda d: explanation,
    )

    assert exp is not None
    assert exp.text == explanation.text
    assert ver_res.is_grounded is True
    assert ver_res.retry_count == 0


def test_verify_with_retry_succeeds_on_second_attempt(
    grounded_decision_and_explanation: tuple[FusionDecision, Explanation],
) -> None:
    decision, valid_explanation = grounded_decision_and_explanation

    bad_explanation = Explanation(
        decision_id=decision.decision_id,
        text="Hallucinated text",
        cited_channels=["NON_EXISTENT_CH"],
        cited_severity=Severity.CRITICAL,
        prompt_version="v1.0.0",
        llm_model="mock-reasoner",
        created_at=utc_now(),
    )

    attempt_count = 0

    def mock_gen(d: FusionDecision) -> Explanation:
        nonlocal attempt_count
        attempt_count += 1
        return bad_explanation if attempt_count == 1 else valid_explanation

    exp, ver_res = verify_with_retry(
        decision=decision,
        generate_fn=mock_gen,
    )

    assert attempt_count == 2
    assert exp is not None
    assert exp.text == valid_explanation.text
    assert ver_res.is_grounded is True
    assert ver_res.retry_count == 1


def test_verify_with_retry_abstains_after_max_retries(
    grounded_decision_and_explanation: tuple[FusionDecision, Explanation],
) -> None:
    decision, _ = grounded_decision_and_explanation

    bad_explanation = Explanation(
        decision_id=decision.decision_id,
        text="Permanently hallucinated text",
        cited_channels=["GHOST_CH"],
        cited_severity=Severity.CRITICAL,
        prompt_version="v1.0.0",
        llm_model="mock-reasoner",
        created_at=utc_now(),
    )

    attempts = 0

    def mock_always_bad(d: FusionDecision) -> Explanation:
        nonlocal attempts
        attempts += 1
        return bad_explanation

    exp, ver_res = verify_with_retry(
        decision=decision,
        generate_fn=mock_always_bad,
        max_retries=MAX_RETRIES,
    )

    # Total attempts = 1 initial + 2 retries = 3
    assert attempts == 3
    assert exp is None  # System abstains!
    assert ver_res.status == VerifierStatus.ABSTAINED
    assert ver_res.retry_count == 2
