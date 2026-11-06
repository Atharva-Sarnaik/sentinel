"""
services.baselines.isolation_forest
======================================
Arm B: Isolation Forest baseline for satellite telemetry anomaly detection.

Design:
  - Fits an ensemble of Isolation Trees on statistical features extracted from training windows.
  - Maps Isolation Forest decision function scores to bounded [0.0, 1.0] anomaly scores.
  - Identifies responsible channels based on feature divergence.
  - Emits frozen SpecialistOpinion contracts for the ablation harness.

Owner:   Sujal Hede (@Sujalhede) / Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    1 (task T1.2)
Status:  complete — Arm B Isolation Forest detector with fit/save/load/predict.
"""

from __future__ import annotations

import math
import pickle
from collections.abc import Sequence
from pathlib import Path

import numpy as np
from sklearn.ensemble import IsolationForest

from libs.common.helpers import extract_window_features
from libs.contracts import Severity, SpecialistOpinion, TelemetryWindow


class IsolationForestBaseline:
    """Isolation Forest anomaly detector for a satellite subsystem."""

    def __init__(
        self,
        n_estimators: int = 100,
        contamination: float = 0.05,
        random_state: int = 42,
    ) -> None:
        self.n_estimators = n_estimators
        self.contamination = contamination
        self.random_state = random_state
        self.model = IsolationForest(
            n_estimators=self.n_estimators,
            contamination=self.contamination,
            random_state=self.random_state,
        )
        self.feature_names: list[str] = []
        self.feature_means: dict[str, float] = {}
        self.feature_stds: dict[str, float] = {}
        self.is_fitted: bool = False

    def _extract_matrix(self, windows: Sequence[TelemetryWindow]) -> np.ndarray:
        """Convert windows into 2D feature matrix adhering to self.feature_names."""
        rows = []
        for w in windows:
            feat_dict = extract_window_features(w.channels)
            row = [feat_dict.get(fn, 0.0) for fn in self.feature_names]
            rows.append(row)
        return np.array(rows, dtype=np.float32)

    def fit(self, windows: Sequence[TelemetryWindow]) -> IsolationForestBaseline:
        """
        Train Isolation Forest on normal training telemetry windows.

        Args:
            windows: Sequence of training TelemetryWindows.

        Returns:
            self
        """
        if not windows:
            raise ValueError("Cannot fit Isolation Forest on empty window sequence.")

        # Determine canonical feature column order from first window
        first_feats = extract_window_features(windows[0].channels)
        self.feature_names = sorted(first_feats.keys())

        # Fit feature means/stds for channel attribution
        all_feats: dict[str, list[float]] = {fn: [] for fn in self.feature_names}
        for w in windows:
            fd = extract_window_features(w.channels)
            for fn in self.feature_names:
                all_feats[fn].append(fd.get(fn, 0.0))

        for fn, vals in all_feats.items():
            mean = sum(vals) / len(vals)
            var = sum((x - mean) ** 2 for x in vals) / max(1, len(vals) - 1)
            self.feature_means[fn] = mean
            self.feature_stds[fn] = math.sqrt(var) if var > 1e-8 else 1.0

        # Build feature matrix and train model
        X = self._extract_matrix(windows)
        self.model.fit(X)
        self.is_fitted = True
        return self

    def predict(
        self,
        window: TelemetryWindow,
        model_run_id: str = "baseline-arm-b-iforest",
    ) -> SpecialistOpinion:
        """
        Assess a TelemetryWindow using the trained Isolation Forest model.

        Args:
            window: Input TelemetryWindow.
            model_run_id: Identifier for the model run.

        Returns:
            SpecialistOpinion contract.
        """
        if not self.is_fitted:
            raise RuntimeError("IsolationForestBaseline must be fitted before predict().")

        feat_dict = extract_window_features(window.channels)
        row = np.array([[feat_dict.get(fn, 0.0) for fn in self.feature_names]], dtype=np.float32)

        # score_samples yields -s(x) where s(x) is Liu et al.'s anomaly score in [0, 1]
        raw_score = -float(self.model.score_samples(row)[0])
        anomaly_score = max(0.0, min(1.0, raw_score))

        # Determine responsible channels based on highest z-score deviation in features
        channel_deviations: dict[str, float] = {}
        for fn, val in feat_dict.items():
            ch = fn.split("__")[0]
            mean = self.feature_means.get(fn, 0.0)
            std = self.feature_stds.get(fn, 1.0)
            z_score = abs(val - mean) / std
            channel_deviations[ch] = max(channel_deviations.get(ch, 0.0), z_score)

        responsible_channels: list[str] = [
            ch for ch, dev in channel_deviations.items() if dev > 2.5
        ]

        # Severity mapping
        if anomaly_score < 0.5:
            severity = Severity.NOMINAL
            responsible_channels = []
        elif anomaly_score < 0.7:
            severity = Severity.WARNING
        else:
            severity = Severity.CRITICAL

        return SpecialistOpinion(
            window_id=window.window_id,
            subsystem=window.subsystem,
            anomaly_score=anomaly_score,
            severity=severity,
            responsible_channels=responsible_channels,
            threshold_used=0.5,
            model_run_id=model_run_id,
        )

    def save(self, path: Path) -> None:
        """Serialize model and metadata to disk."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path: Path) -> IsolationForestBaseline:
        """Load serialized model from disk."""
        with path.open("rb") as f:
            return pickle.load(f)  # type: ignore[no-any-return]


def run_isolation_forest(
    window: TelemetryWindow,
    model_or_path: IsolationForestBaseline | str | Path,
    model_run_id: str = "baseline-arm-b-iforest",
) -> SpecialistOpinion:
    """Helper entry point for classifying a window with Isolation Forest."""
    if isinstance(model_or_path, (str, Path)):
        model = IsolationForestBaseline.load(Path(model_or_path))
    else:
        model = model_or_path
    return model.predict(window, model_run_id=model_run_id)
