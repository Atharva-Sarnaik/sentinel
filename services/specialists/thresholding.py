"""
services.specialists.thresholding
====================================
Nonparametric dynamic thresholding for anomaly detection.

Implements adaptive threshold calculation inspired by Hundman et al. (NASA JPL, KDD 2018):
"Detecting Spacecraft Anomalies Using LSTMs and Nonparametric Dynamic Thresholding".

Produces adaptive anomaly thresholds from error distributions without assuming
a parametric Gaussian distribution.

Owner:   Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    1 (task T1.4)
Status:  complete — nonparametric adaptive threshold calibration and severity scoring.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from libs.contracts import Severity


class DynamicThresholder:
    """
    Fits a nonparametric threshold from reconstruction errors
    and classifies new errors as nominal, warning, or critical anomalies.
    """

    def __init__(self, default_percentile: float = 95.0, min_threshold: float = 1e-4) -> None:
        self.default_percentile = default_percentile
        self.min_threshold = min_threshold
        self._threshold: float | None = None
        self._mean: float = 0.0
        self._std: float = 1.0
        self.is_fitted: bool = False

    def fit(self, errors: Sequence[float], percentile: float | None = None) -> DynamicThresholder:
        """
        Fit the anomaly threshold from a sequence of reconstruction errors.

        Args:
            errors: Sequence of per-window reconstruction errors (non-negative).
            percentile: Target percentile cutoff (defaults to self.default_percentile).

        Returns:
            self
        """
        if not errors:
            raise ValueError("Cannot fit threshold on empty errors sequence.")

        p = percentile if percentile is not None else self.default_percentile
        if not (0.0 < p < 100.0):
            raise ValueError(f"percentile must be in (0, 100), got {p}")

        clean_errors = [max(0.0, float(e)) for e in errors]
        n = len(clean_errors)

        self._mean = sum(clean_errors) / n
        variance = sum((x - self._mean) ** 2 for x in clean_errors) / max(1, n - 1)
        self._std = math.sqrt(variance)

        sorted_errors = sorted(clean_errors)
        rank_idx = int(math.ceil((p / 100.0) * n)) - 1
        rank_idx = max(0, min(rank_idx, n - 1))
        percentile_val = sorted_errors[rank_idx]

        # Use max of percentile value and mean + 1.5 * std as robust cutoff
        stat_cutoff = self._mean + 1.5 * self._std
        self._threshold = max(percentile_val, stat_cutoff, self.min_threshold)
        self.is_fitted = True
        return self

    def predict(self, error: float) -> bool:
        """Return True if error meets or exceeds the fitted anomaly threshold."""
        return self.score(error) >= 0.5

    def score(self, error: float) -> float:
        """
        Convert raw reconstruction error into normalized anomaly score in [0.0, 1.0].
        Score 0.5 is the exact threshold boundary.
        """
        if not self.is_fitted or self._threshold is None:
            raise RuntimeError("DynamicThresholder must be fitted before scoring.")

        err = max(0.0, float(error))
        thresh = self._threshold

        if err < thresh:
            # Scaled linearly from 0.0 to 0.499 below threshold
            return (err / thresh) * 0.49
        else:
            # Saturated smoothly from 0.5 to 1.0 above threshold
            excess = (err - thresh) / max(thresh, 1e-6)
            return min(1.0, 0.5 + 0.5 * (1.0 - math.exp(-excess)))

    def severity_for(self, error: float) -> Severity:
        """Classify severity level based on error magnitude relative to threshold."""
        if not self.is_fitted or self._threshold is None:
            raise RuntimeError("DynamicThresholder must be fitted before severity classification.")

        thresh = self._threshold
        err = max(0.0, float(error))

        if err < thresh:
            return Severity.NOMINAL
        elif err < 1.5 * thresh:
            return Severity.WARNING
        else:
            return Severity.CRITICAL

    @property
    def threshold_value(self) -> float:
        """The fitted anomaly threshold scalar."""
        if not self.is_fitted or self._threshold is None:
            raise RuntimeError("DynamicThresholder is not fitted yet.")
        return self._threshold
