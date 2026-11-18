"""
services.fusion.stacking
========================
Learned stacking coordinator with probability calibration for Sentinel (Task T6.2).

Contrasts with deterministic rule-based fusion:
  • Learns empirical cross-subsystem coupling weights from training data.
  • Provides calibrated anomaly probabilities (Platt scaling / sigmoid calibration).
  • Compared directly against rule-based fusion per ADR-0002.

Owner:   Atharva Sarnaik (@Atharva-Sarnaik) / Sujal Hede (@Sujalhede)
Tier:    6 (task T6.2)
Status:  complete — learned stacking coordinator with calibration and comparative evaluation.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression

from libs.common.helpers import utc_now
from libs.contracts import (
    FusionDecision,
    Severity,
    SpecialistOpinion,
    Subsystem,
)
from services.fusion.attribution import attribute_subsystem
from services.fusion.engine import fuse

SUBSYSTEM_ORDER: tuple[Subsystem, ...] = (
    Subsystem.POWER,
    Subsystem.THERMAL,
    Subsystem.ATTITUDE,
    Subsystem.COMMUNICATIONS,
)


def extract_opinion_features(opinions: Sequence[SpecialistOpinion]) -> np.ndarray:
    """
    Extract a deterministic numerical feature vector from specialist opinions.

    Features per subsystem (4 subsystems x 4 features = 16 features):
      1. Raw anomaly score
      2. Severity ordinal (0: nominal, 1: warning, 2: critical)
      3. Responsible channels count
      4. Score margin (score - threshold_used)

    Cross-subsystem interaction features (2 features):
      5. Power x Thermal score coupling
      6. Attitude x Communications score coupling

    Returns:
      1D numpy array of shape (18,).
    """
    op_map: dict[Subsystem, SpecialistOpinion] = {op.subsystem: op for op in opinions}
    features: list[float] = []

    for sub in SUBSYSTEM_ORDER:
        op = op_map.get(sub)
        if op is None:
            features.extend([0.0, 0.0, 0.0, 0.0])
        else:
            score = float(op.anomaly_score)
            sev_val = (
                0.0
                if op.severity == Severity.NOMINAL
                else (1.0 if op.severity == Severity.WARNING else 2.0)
            )
            n_ch = float(len(op.responsible_channels))
            margin = float(score - op.threshold_used)
            features.extend([score, sev_val, n_ch, margin])

    # Interaction terms for physically coupled subsystems
    p_score = op_map[Subsystem.POWER].anomaly_score if Subsystem.POWER in op_map else 0.0
    t_score = op_map[Subsystem.THERMAL].anomaly_score if Subsystem.THERMAL in op_map else 0.0
    a_score = op_map[Subsystem.ATTITUDE].anomaly_score if Subsystem.ATTITUDE in op_map else 0.0
    c_score = (
        op_map[Subsystem.COMMUNICATIONS].anomaly_score
        if Subsystem.COMMUNICATIONS in op_map
        else 0.0
    )

    features.append(float(p_score * t_score))
    features.append(float(a_score * c_score))

    return np.array(features, dtype=np.float64)


class LearnedStackingCoordinator:
    """
    Learned meta-model coordinator combining specialist opinions with calibrated confidence.
    """

    def __init__(
        self,
        warning_threshold: float = 0.35,
        critical_threshold: float = 0.70,
        random_state: int = 42,
    ) -> None:
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.random_state = random_state
        base_lr = LogisticRegression(random_state=random_state, max_iter=200, C=1.0)
        self.model = CalibratedClassifierCV(estimator=base_lr, method="sigmoid", cv=3)
        self._is_fitted = False

    @property
    def is_fitted(self) -> bool:
        """Return whether the stacking coordinator has been trained."""
        return self._is_fitted

    def fit(
        self,
        opinions_list: Sequence[Sequence[SpecialistOpinion]],
        labels: Sequence[bool],
    ) -> LearnedStackingCoordinator:
        """
        Train and calibrate the stacking coordinator.

        Args:
            opinions_list: Sequence of specialist opinions for each training window.
            labels: Ground-truth binary anomaly labels.
        """
        if len(opinions_list) != len(labels):
            raise ValueError(
                f"Length mismatch: opinions_list ({len(opinions_list)}) vs labels ({len(labels)})"
            )
        if len(opinions_list) < 6:
            raise ValueError(
                "Stacking coordinator requires at least 6 samples for cross-validation."
            )

        x_mat = np.array([extract_opinion_features(ops) for ops in opinions_list])
        y_vec = np.array([1 if y else 0 for y in labels], dtype=np.int32)

        # Check class diversity
        if len(np.unique(y_vec)) < 2:
            # Fallback for single-class datasets: synthesize a small regularizer sample
            x_synth = np.zeros_like(x_mat[:1])
            y_synth = np.array([1 if y_vec[0] == 0 else 0], dtype=np.int32)
            x_mat = np.vstack([x_mat, x_synth])
            y_vec = np.concatenate([y_vec, y_synth])

        self.model.fit(x_mat, y_vec)
        self._is_fitted = True
        return self

    def predict_proba(self, opinions: Sequence[SpecialistOpinion]) -> float:
        """
        Compute calibrated anomaly probability for a window's specialist opinions.

        Returns:
            Calibrated probability P(anomalous) in [0.0, 1.0].
        """
        if not self._is_fitted:
            # Heuristic fallback before fitting: mean of specialist scores
            return float(np.mean([op.anomaly_score for op in opinions]))

        feat = extract_opinion_features(opinions).reshape(1, -1)
        proba = self.model.predict_proba(feat)[0, 1]
        return float(proba)

    def predict_severity(self, opinions: Sequence[SpecialistOpinion]) -> Severity:
        """Assign system Severity based on calibrated stacking probability."""
        prob = self.predict_proba(opinions)
        if prob >= self.critical_threshold:
            return Severity.CRITICAL
        if prob >= self.warning_threshold:
            return Severity.WARNING
        return Severity.NOMINAL

    def fuse_stacking(self, opinions: list[SpecialistOpinion]) -> FusionDecision:
        """
        Produce an immutable FusionDecision using the learned stacking coordinator.
        """
        if not opinions:
            raise ValueError("Cannot fuse an empty list of opinions.")

        window_id = opinions[0].window_id
        prob = self.predict_proba(opinions)
        stacked_severity = self.predict_severity(opinions)

        # Attribute root cause to subsystem with highest score margin
        attributed = attribute_subsystem(opinions)

        corroborating = [
            op.subsystem for op in opinions if op.severity in (Severity.WARNING, Severity.CRITICAL)
        ]

        return FusionDecision(
            window_id=window_id,
            opinions=list(opinions),
            severity=stacked_severity,
            corroborating_subsystems=corroborating,
            attributed_subsystem=attributed,
            fusion_rule_applied=f"learned_stacking_calibrated(prob={prob:.4f})",
            created_at=utc_now(),
        )


def compute_expected_calibration_error(
    probabilities: Sequence[float],
    labels: Sequence[bool],
    n_bins: int = 5,
) -> float:
    """
    Calculate Expected Calibration Error (ECE) across probability predictions.
    """
    probs = np.array(probabilities)
    y_true = np.array([1 if y else 0 for y in labels])
    bin_boundaries = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0

    for i in range(n_bins):
        bin_mask = (probs >= bin_boundaries[i]) & (probs < bin_boundaries[i + 1])
        if i == n_bins - 1:
            bin_mask = bin_mask | (probs == 1.0)
        bin_count = np.sum(bin_mask)
        if bin_count > 0:
            bin_acc = np.mean(y_true[bin_mask])
            bin_conf = np.mean(probs[bin_mask])
            ece += (bin_count / len(probs)) * abs(bin_acc - bin_conf)

    return round(float(ece), 4)


def compare_stacking_vs_rules(
    eval_opinions_list: Sequence[list[SpecialistOpinion]],
    ground_truth: Sequence[bool],
    stacking_coordinator: LearnedStackingCoordinator,
) -> dict[str, Any]:
    """
    Compare learned stacking coordinator against deterministic rule-based fusion (Task T6.2).

    Args:
        eval_opinions_list: Specialist opinions for each test window.
        ground_truth: Ground-truth binary anomaly labels.
        stacking_coordinator: Trained LearnedStackingCoordinator instance.

    Returns:
        Dictionary containing comparative performance and calibration metrics.
    """
    if len(eval_opinions_list) != len(ground_truth):
        raise ValueError("Length mismatch between evaluation opinions and ground truth.")

    rule_preds: list[bool] = []
    stacking_preds: list[bool] = []
    stacking_probs: list[float] = []

    for ops in eval_opinions_list:
        # Rule-based decision
        rule_dec = fuse(ops)
        rule_preds.append(rule_dec.is_anomalous)

        # Stacking decision
        st_dec = stacking_coordinator.fuse_stacking(ops)
        stacking_preds.append(st_dec.is_anomalous)
        stacking_probs.append(stacking_coordinator.predict_proba(ops))

    def _calc_stats(preds: list[bool]) -> dict[str, float]:
        tp = sum(1 for p, y in zip(preds, ground_truth, strict=True) if p and y)
        fp = sum(1 for p, y in zip(preds, ground_truth, strict=True) if p and not y)
        fn = sum(1 for p, y in zip(preds, ground_truth, strict=True) if not p and y)
        tn = sum(1 for p, y in zip(preds, ground_truth, strict=True) if not p and not y)
        p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * p * r) / (p + r) if (p + r) > 0 else 0.0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        acc = (tp + tn) / len(preds) if preds else 0.0
        return {
            "accuracy": round(acc, 4),
            "precision": round(p, 4),
            "recall": round(r, 4),
            "f1": round(f1, 4),
            "false_positive_rate": round(fpr, 4),
        }

    rule_stats = _calc_stats(rule_preds)
    stacking_stats = _calc_stats(stacking_preds)

    # Calibration error
    ece = compute_expected_calibration_error(stacking_probs, ground_truth)
    brier_score = round(
        float(
            np.mean(
                [
                    (prob - (1.0 if y else 0.0)) ** 2
                    for prob, y in zip(stacking_probs, ground_truth, strict=True)
                ]
            )
        ),
        4,
    )
    stacking_stats["expected_calibration_error"] = ece
    stacking_stats["brier_score"] = brier_score

    return {
        "sample_count": len(ground_truth),
        "rule_based_fusion": rule_stats,
        "learned_stacking": stacking_stats,
        "comparison_verdict": (
            "Stacking provides calibrated probabilities with comparable classification accuracy."
            if stacking_stats["f1"] >= rule_stats["f1"] * 0.9
            else "Rule-based fusion maintains higher deterministic fidelity."
        ),
    }
