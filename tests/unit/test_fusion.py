"""
tests.unit.test_fusion
======================
Golden cases, property tests, and determinism tests for the Fusion Engine (task T2.4).

Verifies ADR-0002 compliance:
  • Sole authority on severity and alert level.
  • Same input always yields same decision (deterministic).
  • Golden cross-subsystem corroboration rules.
  • Attribution logic.

Owner:   Sujal Hede (@Sujalhede) / Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    2 (tasks T2.1, T2.2, T2.3, T2.4)
Status:  complete — golden cases, property determinism, and attribution verification.
"""

from __future__ import annotations

import uuid

import pytest

from libs.common.helpers import utc_now
from libs.contracts import Severity, SpecialistOpinion, Subsystem
from services.fusion.corroboration import load_corroboration_rules
from services.fusion.engine import fuse


def _make_opinion(
    subsystem: Subsystem,
    severity: Severity,
    score: float,
    window_id: uuid.UUID,
    channels: list[str] | None = None,
) -> SpecialistOpinion:
    return SpecialistOpinion(
        window_id=window_id,
        subsystem=subsystem,
        anomaly_score=score,
        severity=severity,
        responsible_channels=channels or [],
        threshold_used=0.5,
        model_run_id=f"test-run-{subsystem.value}",
        created_at=utc_now(),
    )


# ---------------------------------------------------------------------------
# Validation & Error Handling Tests
# ---------------------------------------------------------------------------


def test_fuse_empty_opinions_raises() -> None:
    with pytest.raises(ValueError, match="Cannot fuse an empty list"):
        fuse([])


def test_fuse_mismatched_window_ids_raises() -> None:
    op1 = _make_opinion(Subsystem.POWER, Severity.NOMINAL, 0.1, uuid.uuid4())
    op2 = _make_opinion(Subsystem.THERMAL, Severity.NOMINAL, 0.1, uuid.uuid4())
    with pytest.raises(ValueError, match="share the same window_id"):
        fuse([op1, op2])


# ---------------------------------------------------------------------------
# Golden Case 1: Nominal Baseline
# ---------------------------------------------------------------------------


def test_golden_case_nominal_baseline() -> None:
    wid = uuid.uuid4()
    opinions = [
        _make_opinion(Subsystem.POWER, Severity.NOMINAL, 0.05, wid),
        _make_opinion(Subsystem.THERMAL, Severity.NOMINAL, 0.08, wid),
        _make_opinion(Subsystem.ATTITUDE, Severity.NOMINAL, 0.02, wid),
        _make_opinion(Subsystem.COMMUNICATIONS, Severity.NOMINAL, 0.04, wid),
    ]

    decision = fuse(opinions)
    assert decision.severity == Severity.NOMINAL
    assert decision.is_anomalous is False
    assert decision.attributed_subsystem is None
    assert decision.corroborating_subsystems == []
    assert decision.fusion_rule_applied == "nominal_baseline"


# ---------------------------------------------------------------------------
# Golden Case 2: Single Subsystem Isolated Anomaly
# ---------------------------------------------------------------------------


def test_golden_case_isolated_anomaly() -> None:
    wid = uuid.uuid4()
    opinions = [
        _make_opinion(Subsystem.POWER, Severity.WARNING, 0.72, wid, ["P-1"]),
        _make_opinion(Subsystem.THERMAL, Severity.NOMINAL, 0.05, wid),
        _make_opinion(Subsystem.ATTITUDE, Severity.NOMINAL, 0.03, wid),
        _make_opinion(Subsystem.COMMUNICATIONS, Severity.NOMINAL, 0.04, wid),
    ]

    decision = fuse(opinions)
    assert decision.severity == Severity.WARNING
    assert decision.is_anomalous is True
    assert decision.attributed_subsystem == Subsystem.POWER
    assert decision.corroborating_subsystems == []
    assert decision.fusion_rule_applied == "single_subsystem_isolated"


# ---------------------------------------------------------------------------
# Golden Case 3: Power + Thermal Coupled Anomaly (Escalation to Critical)
# ---------------------------------------------------------------------------


def test_golden_case_power_thermal_escalation() -> None:
    wid = uuid.uuid4()
    opinions = [
        _make_opinion(Subsystem.POWER, Severity.WARNING, 0.68, wid, ["P-3", "P-4"]),
        _make_opinion(Subsystem.THERMAL, Severity.WARNING, 0.65, wid, ["T-3"]),
        _make_opinion(Subsystem.ATTITUDE, Severity.NOMINAL, 0.02, wid),
        _make_opinion(Subsystem.COMMUNICATIONS, Severity.NOMINAL, 0.05, wid),
    ]

    decision = fuse(opinions)
    # Coupled rule power_thermal_coupling escalates WARNING to CRITICAL
    assert decision.severity == Severity.CRITICAL
    assert decision.is_anomalous is True
    assert decision.fusion_rule_applied == "power_thermal_coupling"
    assert decision.attributed_subsystem == Subsystem.POWER
    assert Subsystem.POWER in decision.corroborating_subsystems
    assert Subsystem.THERMAL in decision.corroborating_subsystems


# ---------------------------------------------------------------------------
# Golden Case 4: Attitude + Communications Coupling (Antenna Mispointing)
# ---------------------------------------------------------------------------


def test_golden_case_attitude_comms_coupling() -> None:
    wid = uuid.uuid4()
    opinions = [
        _make_opinion(Subsystem.POWER, Severity.NOMINAL, 0.02, wid),
        _make_opinion(Subsystem.THERMAL, Severity.NOMINAL, 0.03, wid),
        _make_opinion(Subsystem.ATTITUDE, Severity.WARNING, 0.75, wid, ["A-3"]),
        _make_opinion(Subsystem.COMMUNICATIONS, Severity.WARNING, 0.70, wid, ["C-1"]),
    ]

    decision = fuse(opinions)
    assert decision.severity == Severity.WARNING
    assert decision.fusion_rule_applied == "attitude_comms_coupling"
    assert decision.attributed_subsystem == Subsystem.ATTITUDE
    assert Subsystem.ATTITUDE in decision.corroborating_subsystems
    assert Subsystem.COMMUNICATIONS in decision.corroborating_subsystems


# ---------------------------------------------------------------------------
# Golden Case 5: Cascading Failure (>= 3 Anomalous Subsystems)
# ---------------------------------------------------------------------------


def test_golden_case_cascading_failure() -> None:
    wid = uuid.uuid4()
    opinions = [
        _make_opinion(Subsystem.POWER, Severity.WARNING, 0.62, wid, ["P-1"]),
        _make_opinion(Subsystem.THERMAL, Severity.WARNING, 0.60, wid, ["T-1"]),
        _make_opinion(Subsystem.ATTITUDE, Severity.WARNING, 0.65, wid, ["A-1"]),
        _make_opinion(Subsystem.COMMUNICATIONS, Severity.NOMINAL, 0.05, wid),
    ]

    decision = fuse(opinions)
    assert decision.severity == Severity.CRITICAL
    assert decision.fusion_rule_applied == "cascading_system_failure"
    assert len(decision.corroborating_subsystems) == 3


# ---------------------------------------------------------------------------
# Property & Determinism Tests (T2.4)
# ---------------------------------------------------------------------------


def test_fusion_determinism_property() -> None:
    """Verifies that identical opinions always yield 100% identical decisions."""
    wid = uuid.uuid4()
    opinions = [
        _make_opinion(Subsystem.POWER, Severity.CRITICAL, 0.95, wid, ["P-1", "P-2"]),
        _make_opinion(Subsystem.THERMAL, Severity.WARNING, 0.65, wid, ["T-2"]),
        _make_opinion(Subsystem.ATTITUDE, Severity.NOMINAL, 0.10, wid),
        _make_opinion(Subsystem.COMMUNICATIONS, Severity.NOMINAL, 0.08, wid),
    ]

    first_decision = fuse(opinions)

    for _ in range(50):
        subsequent_decision = fuse(opinions)
        assert subsequent_decision.severity == first_decision.severity
        assert subsequent_decision.attributed_subsystem == first_decision.attributed_subsystem
        assert subsequent_decision.fusion_rule_applied == first_decision.fusion_rule_applied
        assert (
            subsequent_decision.corroborating_subsystems == first_decision.corroborating_subsystems
        )
        assert subsequent_decision.window_id == first_decision.window_id


def test_evidence_summary_generation() -> None:
    wid = uuid.uuid4()
    opinions = [
        _make_opinion(Subsystem.POWER, Severity.WARNING, 0.68, wid, ["P-1"]),
        _make_opinion(Subsystem.THERMAL, Severity.WARNING, 0.65, wid, ["T-1"]),
        _make_opinion(Subsystem.ATTITUDE, Severity.NOMINAL, 0.02, wid),
        _make_opinion(Subsystem.COMMUNICATIONS, Severity.NOMINAL, 0.05, wid),
    ]

    decision = fuse(opinions)
    summary = decision.evidence_summary()
    assert summary["severity"] == "critical"
    assert summary["attributed_subsystem"] == "power"
    assert "power_thermal_coupling" in summary["fusion_rule_applied"]
    assert len(summary["opinions"]) == 4


def test_load_corroboration_rules() -> None:
    rules = load_corroboration_rules()
    assert len(rules) >= 5
    rule_names = {r.name for r in rules}
    assert "power_thermal_coupling" in rule_names
    assert "attitude_comms_coupling" in rule_names
    assert "cascading_system_failure" in rule_names
    assert "nominal_baseline" in rule_names
