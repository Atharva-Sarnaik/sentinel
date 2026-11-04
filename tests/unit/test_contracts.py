"""
tests.unit.test_contracts
==========================
Unit tests for libs.contracts.models.

Owner:   Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    0 (task T0.3)
Status:  scaffolding — basic construction tests in place.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from libs.contracts.models import (
    AuditEntry,
    Explanation,
    FusionDecision,
    RunManifest,
    Severity,
    SpecialistOpinion,
    Subsystem,
    TelemetryWindow,
    VerifierResult,
    VerifierStatus,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_window() -> TelemetryWindow:
    return TelemetryWindow(
        subsystem=Subsystem.POWER,
        start_time=datetime(2024, 1, 1, 0, 0, tzinfo=UTC),
        end_time=datetime(2024, 1, 1, 0, 1, tzinfo=UTC),
        channels={"P_BUS_VOLTAGE": [28.1, 28.2, 28.0]},
        source_dataset="SMAP",
    )


@pytest.fixture
def sample_opinion(sample_window: TelemetryWindow) -> SpecialistOpinion:
    return SpecialistOpinion(
        window_id=sample_window.window_id,
        subsystem=Subsystem.POWER,
        anomaly_score=0.85,
        severity=Severity.WARNING,
        responsible_channels=["P_BUS_VOLTAGE"],
        threshold_used=0.75,
        model_run_id="mlflow-run-placeholder",
    )


@pytest.fixture
def sample_decision(sample_opinion: SpecialistOpinion) -> FusionDecision:
    return FusionDecision(
        window_id=sample_opinion.window_id,
        opinions=[sample_opinion],
        severity=Severity.WARNING,
        corroborating_subsystems=[Subsystem.POWER],
        attributed_subsystem=Subsystem.POWER,
        fusion_rule_applied="single-subsystem-warning",
    )


@pytest.fixture
def sample_explanation(sample_decision: FusionDecision) -> Explanation:
    return Explanation(
        decision_id=sample_decision.decision_id,
        text="The power subsystem shows elevated bus voltage anomaly.",
        cited_channels=["P_BUS_VOLTAGE"],
        cited_severity=Severity.WARNING,
        prompt_version="v0.1-placeholder",
        llm_model="gpt-4o-mini",
    )


# ---------------------------------------------------------------------------
# TelemetryWindow
# ---------------------------------------------------------------------------


class TestTelemetryWindow:
    def test_construction(self, sample_window: TelemetryWindow) -> None:
        assert sample_window.subsystem == Subsystem.POWER
        assert sample_window.source_dataset == "SMAP"

    def test_frozen(self, sample_window: TelemetryWindow) -> None:
        with pytest.raises((TypeError, ValidationError)):
            sample_window.subsystem = Subsystem.THERMAL  # type: ignore[misc]

    def test_window_id_is_uuid(self, sample_window: TelemetryWindow) -> None:
        assert isinstance(sample_window.window_id, uuid.UUID)

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            TelemetryWindow(
                subsystem=Subsystem.POWER,
                start_time=datetime(2024, 1, 1, tzinfo=UTC),
                end_time=datetime(2024, 1, 1, 0, 1, tzinfo=UTC),
                source_dataset="SMAP",
                nonexistent_field="oops",  # type: ignore[call-arg]
            )


# ---------------------------------------------------------------------------
# SpecialistOpinion
# ---------------------------------------------------------------------------


class TestSpecialistOpinion:
    def test_construction(self, sample_opinion: SpecialistOpinion) -> None:
        assert 0.0 <= sample_opinion.anomaly_score <= 1.0
        assert sample_opinion.subsystem == Subsystem.POWER

    def test_anomaly_score_bounds(self, sample_window: TelemetryWindow) -> None:
        with pytest.raises(ValidationError):
            SpecialistOpinion(
                window_id=sample_window.window_id,
                subsystem=Subsystem.POWER,
                anomaly_score=1.5,  # out of [0, 1]
                severity=Severity.WARNING,
                threshold_used=0.75,
                model_run_id="run",
            )

    def test_frozen(self, sample_opinion: SpecialistOpinion) -> None:
        with pytest.raises((TypeError, ValidationError)):
            sample_opinion.anomaly_score = 0.0  # type: ignore[misc]


# ---------------------------------------------------------------------------
# FusionDecision
# ---------------------------------------------------------------------------


class TestFusionDecision:
    def test_construction(self, sample_decision: FusionDecision) -> None:
        assert sample_decision.severity == Severity.WARNING
        assert len(sample_decision.opinions) == 1

    def test_frozen(self, sample_decision: FusionDecision) -> None:
        with pytest.raises((TypeError, ValidationError)):
            sample_decision.severity = Severity.CRITICAL  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Explanation
# ---------------------------------------------------------------------------


class TestExplanation:
    def test_construction(self, sample_explanation: Explanation) -> None:
        assert sample_explanation.cited_severity == Severity.WARNING
        assert "P_BUS_VOLTAGE" in sample_explanation.cited_channels


# ---------------------------------------------------------------------------
# VerifierResult
# ---------------------------------------------------------------------------


class TestVerifierResult:
    def test_construction(self, sample_explanation: Explanation) -> None:
        result = VerifierResult(
            explanation_id=sample_explanation.explanation_id,
            status=VerifierStatus.GROUNDED,
            retry_count=0,
        )
        assert result.status == VerifierStatus.GROUNDED

    def test_retry_count_bound(self, sample_explanation: Explanation) -> None:
        with pytest.raises(ValidationError):
            VerifierResult(
                explanation_id=sample_explanation.explanation_id,
                status=VerifierStatus.UNGROUNDED,
                retry_count=3,  # exceeds max of 2 (ADR-0002)
            )


# ---------------------------------------------------------------------------
# AuditEntry
# ---------------------------------------------------------------------------


class TestAuditEntry:
    def test_construction(
        self,
        sample_decision: FusionDecision,
    ) -> None:
        verifier = VerifierResult(
            explanation_id=uuid.uuid4(),
            status=VerifierStatus.GROUNDED,
            retry_count=0,
        )
        entry = AuditEntry(
            run_id="test-run-001",
            window_id=sample_decision.window_id,
            decision_id=sample_decision.decision_id,
            verifier_id=verifier.verifier_id,
            final_severity=Severity.WARNING,
            abstained=False,
        )
        assert entry.abstained is False
        assert entry.final_severity == Severity.WARNING


# ---------------------------------------------------------------------------
# RunManifest
# ---------------------------------------------------------------------------


class TestRunManifest:
    def test_construction(self) -> None:
        manifest = RunManifest(
            description="Test run",
            dataset_dvc_hash="abc123",
            config_hash="def456",
            mlflow_experiment_id="1",
            mlflow_run_ids={"power": "run-p", "thermal": "run-t"},
        )
        assert manifest.description == "Test run"
        assert "power" in manifest.mlflow_run_ids
