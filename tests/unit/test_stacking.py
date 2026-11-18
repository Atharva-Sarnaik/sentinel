"""
tests.unit.test_stacking
========================
Unit tests for Task T6.2: Learned Stacking Coordinator with Calibration (services.fusion.stacking).

Tests:
  - Feature extraction from SpecialistOpinion sequences (shape and values).
  - Model fitting with Platt scaling calibration.
  - Anomaly probability and severity prediction.
  - Creation of valid, frozen FusionDecision contracts.
  - Expected Calibration Error (ECE) calculation.
  - Comparative evaluation against rule-based fusion.

Owner:   Atharva Sarnaik (@Atharva-Sarnaik) / Sujal Hede (@Sujalhede)
Tier:    6 (task T6.2)
"""

from __future__ import annotations

import uuid

import numpy as np
import pytest

from libs.common.helpers import utc_now
from libs.contracts import FusionDecision, Severity, SpecialistOpinion, Subsystem
from services.fusion.stacking import (
    LearnedStackingCoordinator,
    compare_stacking_vs_rules,
    compute_expected_calibration_error,
    extract_opinion_features,
)


def _make_dummy_opinions(
    window_id: uuid.UUID,
    is_anom: bool,
) -> list[SpecialistOpinion]:
    """Create a list of 4 specialist opinions with anomalous or nominal flags."""
    ops: list[SpecialistOpinion] = []
    subsystems = [
        Subsystem.POWER,
        Subsystem.THERMAL,
        Subsystem.ATTITUDE,
        Subsystem.COMMUNICATIONS,
    ]
    for sub in subsystems:
        if is_anom and sub in (Subsystem.POWER, Subsystem.THERMAL):
            score = 0.85
            sev = Severity.CRITICAL
            channels = [f"{sub.value[0].upper()}-1"]
        else:
            score = 0.05
            sev = Severity.NOMINAL
            channels = []

        ops.append(
            SpecialistOpinion(
                window_id=window_id,
                subsystem=sub,
                anomaly_score=score,
                severity=sev,
                responsible_channels=channels,
                threshold_used=0.5,
                model_run_id=f"{sub.value}-unit",
                created_at=utc_now(),
            )
        )
    return ops


def test_extract_opinion_features_shape_and_content() -> None:
    """Verify opinion feature extractor produces expected 18-element vector."""
    w_id = uuid.uuid4()
    opinions = _make_dummy_opinions(w_id, is_anom=True)
    features = extract_opinion_features(opinions)

    assert isinstance(features, np.ndarray)
    assert features.shape == (18,)
    # Power score is 0.85, Thermal score is 0.85 -> Interaction is 0.85 * 0.85 = 0.7225
    assert pytest.approx(features[16], rel=1e-3) == 0.7225


def test_stacking_coordinator_fit_and_predict() -> None:
    """Verify coordinator training, probability calibration, and severity assignment."""
    train_ops = []
    labels = []
    # 10 train samples: 5 nominal, 5 anomalous
    for i in range(10):
        w_id = uuid.uuid4()
        is_anom = i % 2 == 1
        train_ops.append(_make_dummy_opinions(w_id, is_anom=is_anom))
        labels.append(is_anom)

    coordinator = LearnedStackingCoordinator(random_state=42)
    assert not coordinator.is_fitted

    coordinator.fit(train_ops, labels)
    assert coordinator.is_fitted

    # Test prediction on nominal window
    nom_ops = _make_dummy_opinions(uuid.uuid4(), is_anom=False)
    p_nom = coordinator.predict_proba(nom_ops)
    sev_nom = coordinator.predict_severity(nom_ops)
    assert 0.0 <= p_nom <= 1.0
    assert p_nom < 0.50
    assert sev_nom == Severity.NOMINAL

    # Test prediction on anomalous window
    anom_ops = _make_dummy_opinions(uuid.uuid4(), is_anom=True)
    p_anom = coordinator.predict_proba(anom_ops)
    sev_anom = coordinator.predict_severity(anom_ops)
    assert 0.0 <= p_anom <= 1.0
    assert p_anom > 0.50
    assert sev_anom in (Severity.WARNING, Severity.CRITICAL)


def test_fuse_stacking_contract_fidelity() -> None:
    """Verify fuse_stacking creates a valid, compliant FusionDecision."""
    w_id = uuid.uuid4()
    opinions = _make_dummy_opinions(w_id, is_anom=True)
    coordinator = LearnedStackingCoordinator()

    decision = coordinator.fuse_stacking(opinions)
    assert isinstance(decision, FusionDecision)
    assert decision.window_id == w_id
    assert "learned_stacking_calibrated" in decision.fusion_rule_applied
    assert len(decision.opinions) == 4
    assert decision.severity in (Severity.NOMINAL, Severity.WARNING, Severity.CRITICAL)


def test_expected_calibration_error() -> None:
    """Verify ECE calculation for well-calibrated and poorly-calibrated predictions."""
    # Perfect calibration: prob 1.0 for True, prob 0.0 for False
    probs = [0.0, 0.0, 1.0, 1.0]
    labels = [False, False, True, True]
    ece_perfect = compute_expected_calibration_error(probs, labels)
    assert ece_perfect == 0.0

    # Miscalibrated
    probs_bad = [0.9, 0.9, 0.1, 0.1]
    ece_bad = compute_expected_calibration_error(probs_bad, labels)
    assert ece_bad > 0.5


def test_compare_stacking_vs_rules() -> None:
    """Verify direct comparison utility between learned stacking and rule-based fusion."""
    train_ops = []
    train_labels = []
    for i in range(12):
        w_id = uuid.uuid4()
        is_anom = i % 2 == 1
        train_ops.append(_make_dummy_opinions(w_id, is_anom=is_anom))
        train_labels.append(is_anom)

    coordinator = LearnedStackingCoordinator(random_state=42)
    coordinator.fit(train_ops, train_labels)

    test_ops = []
    test_labels = []
    for i in range(8):
        w_id = uuid.uuid4()
        is_anom = i % 3 == 0
        test_ops.append(_make_dummy_opinions(w_id, is_anom=is_anom))
        test_labels.append(is_anom)

    comparison = compare_stacking_vs_rules(test_ops, test_labels, coordinator)

    assert "rule_based_fusion" in comparison
    assert "learned_stacking" in comparison
    assert "comparison_verdict" in comparison

    rule_res = comparison["rule_based_fusion"]
    stack_res = comparison["learned_stacking"]

    assert "accuracy" in rule_res
    assert "precision" in rule_res
    assert "recall" in rule_res
    assert "f1" in rule_res
    assert "expected_calibration_error" in stack_res
    assert "brier_score" in stack_res
