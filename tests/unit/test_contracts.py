"""
tests.unit.test_contracts
==========================
Unit tests for libs.contracts.models (Task T0.3).

Owner:   Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    0 (task T0.3)
Status:  complete — comprehensive contract tests.
"""

from __future__ import annotations

import json
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
        channels={"P_BUS_VOLTAGE": [28.1, 28.2, 28.0], "P_BUS_CURRENT": [4.0, 4.1, 3.9]},
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
        model_run_id="mlflow-run-001",
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
# TelemetryWindow Tests
# ---------------------------------------------------------------------------


class TestTelemetryWindow:
    def test_construction(self, sample_window: TelemetryWindow) -> None:
        assert sample_window.subsystem == Subsystem.POWER
        assert sample_window.source_dataset == "SMAP"
        assert sample_window.window_length == 3
        assert set(sample_window.channel_names) == {"P_BUS_VOLTAGE", "P_BUS_CURRENT"}

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
                extra_unknown_field="fail",  # type: ignore[call-arg]
            )

    def test_end_time_before_start_time_raises(self) -> None:
        with pytest.raises(ValidationError, match="cannot precede start_time"):
            TelemetryWindow(
                subsystem=Subsystem.POWER,
                start_time=datetime(2024, 1, 1, 0, 10, tzinfo=UTC),
                end_time=datetime(2024, 1, 1, 0, 0, tzinfo=UTC),
                source_dataset="SMAP",
            )

    def test_mismatched_channel_lengths_raises(self) -> None:
        with pytest.raises(ValidationError, match="mismatched time-series lengths"):
            TelemetryWindow(
                subsystem=Subsystem.POWER,
                start_time=datetime(2024, 1, 1, 0, 0, tzinfo=UTC),
                end_time=datetime(2024, 1, 1, 0, 1, tzinfo=UTC),
                channels={
                    "CH_A": [1.0, 2.0, 3.0],
                    "CH_B": [1.0, 2.0],  # only 2 points
                },
                source_dataset="SMAP",
            )

    def test_json_roundtrip(self, sample_window: TelemetryWindow) -> None:
        raw_json = sample_window.model_dump_json()
        reconstructed = TelemetryWindow.model_validate_json(raw_json)
        assert reconstructed.window_id == sample_window.window_id
        assert reconstructed.channels == sample_window.channels


# ---------------------------------------------------------------------------
# SpecialistOpinion Tests
# ---------------------------------------------------------------------------


class TestSpecialistOpinion:
    def test_construction(self, sample_opinion: SpecialistOpinion) -> None:
        assert 0.0 <= sample_opinion.anomaly_score <= 1.0
        assert sample_opinion.subsystem == Subsystem.POWER
        assert sample_opinion.is_anomalous is True

    def test_anomaly_score_bounds(self, sample_window: TelemetryWindow) -> None:
        with pytest.raises(ValidationError):
            SpecialistOpinion(
                window_id=sample_window.window_id,
                subsystem=Subsystem.POWER,
                anomaly_score=1.5,
                severity=Severity.WARNING,
                threshold_used=0.75,
                model_run_id="run",
            )

    def test_threshold_non_negative(self, sample_window: TelemetryWindow) -> None:
        with pytest.raises(ValidationError):
            SpecialistOpinion(
                window_id=sample_window.window_id,
                subsystem=Subsystem.POWER,
                anomaly_score=0.5,
                severity=Severity.NOMINAL,
                threshold_used=-0.1,
                model_run_id="run",
            )

    def test_frozen(self, sample_opinion: SpecialistOpinion) -> None:
        with pytest.raises((TypeError, ValidationError)):
            sample_opinion.anomaly_score = 0.0  # type: ignore[misc]


# ---------------------------------------------------------------------------
# FusionDecision Tests
# ---------------------------------------------------------------------------


class TestFusionDecision:
    def test_construction(self, sample_decision: FusionDecision) -> None:
        assert sample_decision.severity == Severity.WARNING
        assert len(sample_decision.opinions) == 1
        assert sample_decision.is_anomalous is True

    def test_evidence_summary(self, sample_decision: FusionDecision) -> None:
        summary = sample_decision.evidence_summary()
        assert summary["severity"] == "warning"
        assert summary["attributed_subsystem"] == "power"
        assert len(summary["opinions"]) == 1
        # Check it is json serializable
        json_str = json.dumps(summary)
        assert "single-subsystem-warning" in json_str

    def test_frozen(self, sample_decision: FusionDecision) -> None:
        with pytest.raises((TypeError, ValidationError)):
            sample_decision.severity = Severity.CRITICAL  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Explanation Tests
# ---------------------------------------------------------------------------


class TestExplanation:
    def test_construction(self, sample_explanation: Explanation) -> None:
        assert sample_explanation.cited_severity == Severity.WARNING
        assert "P_BUS_VOLTAGE" in sample_explanation.cited_channels


# ---------------------------------------------------------------------------
# VerifierResult Tests
# ---------------------------------------------------------------------------


class TestVerifierResult:
    def test_construction(self, sample_explanation: Explanation) -> None:
        result = VerifierResult(
            explanation_id=sample_explanation.explanation_id,
            status=VerifierStatus.GROUNDED,
            retry_count=0,
        )
        assert result.status == VerifierStatus.GROUNDED
        assert result.is_grounded is True

    def test_retry_count_bound(self, sample_explanation: Explanation) -> None:
        with pytest.raises(ValidationError):
            VerifierResult(
                explanation_id=sample_explanation.explanation_id,
                status=VerifierStatus.UNGROUNDED,
                retry_count=3,  # exceeds max of 2 (ADR-0002)
            )


# ---------------------------------------------------------------------------
# AuditEntry Tests
# ---------------------------------------------------------------------------


class TestAuditEntry:
    def test_construction(self, sample_decision: FusionDecision) -> None:
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
# RunManifest Tests
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
