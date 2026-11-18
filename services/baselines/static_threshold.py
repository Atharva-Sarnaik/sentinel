"""
services.baselines.static_threshold
======================================
Arm A: static two-sided per-channel threshold baseline.

Design:
  - Configurable lower and upper bounds per channel computed from normal training telemetry.
  - Detects anomalies when telemetry falls below lower bound or exceeds upper bound.
  - Strict numerical validation (rejection of NaN, Inf, and empty sequences).
  - JSON model persistence with schema versioning and round-trip fidelity.
  - Window-level evaluation helper returning classification metrics.
  - Outputs a frozen SpecialistOpinion contract for the ablation harness.

Owner:   Sujal Hede (@Sujalhede) / Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    1 (task T1.1)
Status:  complete — Arm A static two-sided threshold detector, calibrator, and evaluator.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from libs.contracts import Severity, SpecialistOpinion, TelemetryWindow


@dataclass(frozen=True)
class ChannelThreshold:
    """
    Validated two-sided static threshold bounds for a single telemetry channel.

    Attributes:
        lower: Lower boundary limit for nominal observations.
        upper: Upper boundary limit for nominal observations.
    """

    lower: float
    upper: float

    def __post_init__(self) -> None:
        """Validate that bounds are finite numbers and lower <= upper."""
        if (
            not isinstance(self.lower, (int, float))
            or math.isnan(self.lower)
            or math.isinf(self.lower)
        ):
            raise ValueError(f"lower threshold must be a finite number, got {self.lower}")
        if (
            not isinstance(self.upper, (int, float))
            or math.isnan(self.upper)
            or math.isinf(self.upper)
        ):
            raise ValueError(f"upper threshold must be a finite number, got {self.upper}")
        if self.lower > self.upper:
            raise ValueError(
                f"Invalid threshold: lower bound ({self.lower}) cannot exceed upper bound ({self.upper})"
            )

    def __ge__(self, other: Any) -> bool:
        """Support backward-compatible comparison thresholds[ch] >= val (checks upper bound)."""
        if isinstance(other, (int, float)):
            return self.upper >= other
        return NotImplemented

    def __le__(self, other: Any) -> bool:
        """Support backward-compatible comparison thresholds[ch] <= val (checks lower bound)."""
        if isinstance(other, (int, float)):
            return self.lower <= other
        return NotImplemented

    def to_dict(self) -> dict[str, float]:
        """Serialize bounds to a dictionary."""
        return {"lower": float(self.lower), "upper": float(self.upper)}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChannelThreshold:
        """Instantiate a ChannelThreshold from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(f"Expected dict for ChannelThreshold, got {type(data)}")
        if "lower" not in data or "upper" not in data:
            raise ValueError("ChannelThreshold dictionary must contain 'lower' and 'upper' keys")
        return cls(lower=float(data["lower"]), upper=float(data["upper"]))


def calibrate_static_thresholds(
    windows: Sequence[TelemetryWindow],
    lower_percentile: float = 0.5,
    upper_percentile: float = 99.5,
    min_range: float = 1e-4,
    percentile: float | None = None,
) -> dict[str, ChannelThreshold]:
    """
    Calibrate static two-sided per-channel anomaly thresholds from training windows.

    Args:
        windows: Sequence of normal/healthy TelemetryWindows.
        lower_percentile: Lower percentile (e.g. 0.5) for the lower threshold boundary.
        upper_percentile: Upper percentile (e.g. 99.5) for the upper threshold boundary.
        min_range: Minimum threshold interval to prevent zero-width bounds on flat lines.
        percentile: Legacy parameter for upper percentile (backward compatibility).

    Returns:
        dict mapping channel name to calibrated ChannelThreshold.

    Raises:
        ValueError: If percentiles are out of bounds or telemetry contains NaN/Inf or empty series.
    """
    if percentile is not None:
        upper_percentile = percentile

    if not (0.0 <= lower_percentile <= 100.0):
        raise ValueError(f"lower_percentile must be between 0.0 and 100.0, got {lower_percentile}")
    if not (0.0 <= upper_percentile <= 100.0):
        raise ValueError(f"upper_percentile must be between 0.0 and 100.0, got {upper_percentile}")
    if lower_percentile > upper_percentile:
        raise ValueError(
            f"lower_percentile ({lower_percentile}) cannot exceed upper_percentile ({upper_percentile})"
        )

    if not windows:
        return {}

    channel_values: dict[str, list[float]] = {}
    for w in windows:
        for ch, series in w.channels.items():
            if len(series) == 0:
                raise ValueError(f"Channel '{ch}' in window '{w.window_id}' has an empty sequence")
            for x in series:
                if not isinstance(x, (int, float)) or math.isnan(x) or math.isinf(x):
                    raise ValueError(
                        f"Invalid telemetry value in channel '{ch}' during calibration: {x} "
                        "(NaN and Inf are rejected)"
                    )
            if ch not in channel_values:
                channel_values[ch] = []
            channel_values[ch].extend(float(x) for x in series)

    thresholds: dict[str, ChannelThreshold] = {}
    for ch, vals in channel_values.items():
        if not vals:
            raise ValueError(f"Channel '{ch}' has no telemetry samples across training windows")

        sorted_vals = sorted(vals)
        n = len(sorted_vals)

        lower_idx = int(math.floor((lower_percentile / 100.0) * (n - 1)))
        lower_idx = max(0, min(lower_idx, n - 1))
        lower_val = sorted_vals[lower_idx]

        upper_idx = int(math.ceil((upper_percentile / 100.0) * (n - 1)))
        upper_idx = max(0, min(upper_idx, n - 1))
        upper_val = sorted_vals[upper_idx]

        if upper_val - lower_val < min_range:
            center = (upper_val + lower_val) / 2.0
            lower_val = center - (min_range / 2.0)
            upper_val = center + (min_range / 2.0)

        thresholds[ch] = ChannelThreshold(lower=float(lower_val), upper=float(upper_val))

    return thresholds


def run_static_threshold(
    window: TelemetryWindow,
    thresholds: Mapping[str, ChannelThreshold | float | tuple[float, float]],
    model_run_id: str = "baseline-arm-a-static",
) -> SpecialistOpinion:
    """
    Classify a TelemetryWindow using static two-sided per-channel thresholding (Arm A).

    Args:
        window: Input TelemetryWindow.
        thresholds: dict mapping channel name to ChannelThreshold or scalar/tuple limits.
        model_run_id: Provenance identifier for the baseline run.

    Returns:
        SpecialistOpinion representing the baseline's assessment.

    Raises:
        ValueError: If telemetry values are NaN/Inf or if a channel sequence is empty.
    """
    # Numerical validation of all channel sequences
    for ch, series in window.channels.items():
        if len(series) == 0:
            raise ValueError(f"Channel '{ch}' in window '{window.window_id}' has an empty sequence")
        for x in series:
            if not isinstance(x, (int, float)) or math.isnan(x) or math.isinf(x):
                raise ValueError(
                    f"Invalid telemetry value in channel '{ch}' during inference: {x} "
                    "(NaN and Inf are rejected)"
                )

    if not window.channels or not thresholds:
        return SpecialistOpinion(
            window_id=window.window_id,
            subsystem=window.subsystem,
            anomaly_score=0.0,
            severity=Severity.NOMINAL,
            responsible_channels=[],
            threshold_used=0.5,
            model_run_id=model_run_id,
        )

    responsible_channels: list[str] = []
    max_relative_violation: float = 0.0

    for ch, series in window.channels.items():
        thresh_obj = thresholds.get(ch)
        if thresh_obj is None:
            continue

        if isinstance(thresh_obj, ChannelThreshold):
            lower = thresh_obj.lower
            upper = thresh_obj.upper
        elif isinstance(thresh_obj, (tuple, list)) and len(thresh_obj) == 2:
            lower = float(thresh_obj[0])
            upper = float(thresh_obj[1])
            if math.isnan(lower) or math.isinf(lower) or math.isnan(upper) or math.isinf(upper):
                raise ValueError(f"Threshold bounds for channel '{ch}' must be finite numbers")
            if lower > upper:
                raise ValueError(
                    f"Invalid threshold for channel '{ch}': lower ({lower}) > upper ({upper})"
                )
        elif isinstance(thresh_obj, (int, float)):
            val = float(thresh_obj)
            if math.isnan(val) or math.isinf(val):
                raise ValueError(f"Threshold for channel '{ch}' must be a finite number")
            lower = -abs(val)
            upper = abs(val)
        else:
            raise ValueError(
                f"Unsupported threshold specification for channel '{ch}': {type(thresh_obj)}"
            )

        ch_peak_violation = 0.0
        violated = False

        for x in series:
            if x > upper:
                violated = True
                denom = max(abs(upper), 1e-6)
                ratio = (x - upper) / denom
                if ratio > ch_peak_violation:
                    ch_peak_violation = ratio
            elif x < lower:
                violated = True
                denom = max(abs(lower), 1e-6)
                ratio = (lower - x) / denom
                if ratio > ch_peak_violation:
                    ch_peak_violation = ratio

        if violated:
            responsible_channels.append(ch)
            if ch_peak_violation > max_relative_violation:
                max_relative_violation = ch_peak_violation

    # Compute normalized anomaly score bounded in [0.0, 1.0]
    if not responsible_channels:
        anomaly_score = 0.0
        severity = Severity.NOMINAL
    else:
        # Logistic / exponential compression: saturates towards 1.0 as violation ratio grows
        anomaly_score = min(1.0, 0.5 + 0.5 * (1.0 - math.exp(-max_relative_violation)))

        # Determine severity based on responsible channel count and excess magnitude
        if len(responsible_channels) >= 2 or max_relative_violation > 1.0:
            severity = Severity.CRITICAL
        elif max_relative_violation > 0.2:
            severity = Severity.WARNING
        else:
            severity = Severity.ADVISORY

    return SpecialistOpinion(
        window_id=window.window_id,
        subsystem=window.subsystem,
        anomaly_score=anomaly_score,
        severity=severity,
        responsible_channels=responsible_channels,
        threshold_used=0.5,
        model_run_id=model_run_id,
    )


class StaticThresholdBaseline:
    """
    Object-oriented wrapper for Arm A static thresholding baseline.
    """

    def __init__(
        self,
        thresholds: dict[str, ChannelThreshold] | None = None,
        model_run_id: str = "baseline-arm-a-static",
        lower_percentile: float = 0.5,
        upper_percentile: float = 99.5,
    ) -> None:
        self.thresholds: dict[str, ChannelThreshold] = thresholds or {}
        self.model_run_id = model_run_id
        self.lower_percentile = lower_percentile
        self.upper_percentile = upper_percentile

    def fit(
        self,
        windows: Sequence[TelemetryWindow],
        lower_percentile: float = 0.5,
        upper_percentile: float = 99.5,
        min_range: float = 1e-4,
        percentile: float | None = None,
    ) -> StaticThresholdBaseline:
        """Calibrate channel thresholds from normal training telemetry windows."""
        self.lower_percentile = lower_percentile
        self.upper_percentile = upper_percentile if percentile is None else percentile
        self.thresholds = calibrate_static_thresholds(
            windows,
            lower_percentile=self.lower_percentile,
            upper_percentile=self.upper_percentile,
            min_range=min_range,
            percentile=percentile,
        )
        return self

    def predict(
        self,
        window: TelemetryWindow,
        model_run_id: str | None = None,
    ) -> SpecialistOpinion:
        """Evaluate a TelemetryWindow and produce a SpecialistOpinion."""
        run_id = model_run_id or self.model_run_id
        return run_static_threshold(window, self.thresholds, model_run_id=run_id)

    def save(self, path: Path | str) -> None:
        """
        Persist calibrated thresholds and calibration metadata to a JSON file.

        Args:
            path: Destination file path.
        """
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "1.0",
            "model_type": "StaticThresholdBaseline",
            "calibration_metadata": {
                "lower_percentile": float(self.lower_percentile),
                "upper_percentile": float(self.upper_percentile),
                "model_run_id": self.model_run_id,
            },
            "thresholds": {ch: thresh.to_dict() for ch, thresh in self.thresholds.items()},
        }
        p.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path | str) -> StaticThresholdBaseline:
        """
        Load calibrated thresholds and metadata from a JSON file.

        Args:
            path: Source file path.

        Returns:
            Instantiated StaticThresholdBaseline with loaded thresholds.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If JSON is malformed, schema is unsupported, or bounds are invalid.
        """
        p = Path(path)
        if not p.is_file():
            raise FileNotFoundError(f"Static threshold file not found: {path}")

        try:
            raw_text = p.read_text(encoding="utf-8")
            data = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Malformed JSON in threshold file {path}: {exc}") from exc
        except Exception as exc:
            raise ValueError(f"Failed to read threshold file {path}: {exc}") from exc

        if not isinstance(data, dict):
            raise ValueError(f"Invalid threshold file structure in {path}: expected JSON object")

        schema_ver = data.get("schema_version")
        if schema_ver != "1.0":
            raise ValueError(f"Unsupported schema version: '{schema_ver}', expected '1.0'")

        raw_thresholds = data.get("thresholds")
        if not isinstance(raw_thresholds, dict):
            raise ValueError(f"Invalid threshold file {path}: 'thresholds' must be an object")

        parsed_thresholds: dict[str, ChannelThreshold] = {}
        for ch, item in raw_thresholds.items():
            if not isinstance(item, dict) or "lower" not in item or "upper" not in item:
                raise ValueError(f"Invalid threshold entry for channel '{ch}': {item}")
            try:
                lower = float(item["lower"])
                upper = float(item["upper"])
                parsed_thresholds[ch] = ChannelThreshold(lower=lower, upper=upper)
            except (ValueError, TypeError) as exc:
                raise ValueError(f"Invalid numeric bounds for channel '{ch}': {exc}") from exc

        meta = data.get("calibration_metadata", {})
        lower_p = meta.get("lower_percentile", 0.5) if isinstance(meta, dict) else 0.5
        upper_p = meta.get("upper_percentile", 99.5) if isinstance(meta, dict) else 99.5
        model_run_id = (
            meta.get("model_run_id", "baseline-arm-a-static")
            if isinstance(meta, dict)
            else "baseline-arm-a-static"
        )

        return cls(
            thresholds=parsed_thresholds,
            model_run_id=model_run_id,
            lower_percentile=lower_p,
            upper_percentile=upper_p,
        )


def evaluate_static_threshold(
    test_windows: Sequence[TelemetryWindow],
    thresholds: Mapping[str, ChannelThreshold | float | tuple[float, float]]
    | StaticThresholdBaseline,
    ground_truth_labels: Sequence[bool | int],
) -> dict[str, float | int]:
    """
    Evaluate static threshold baseline predictions at the window level.

    Args:
        test_windows: Sequence of TelemetryWindows to evaluate.
        thresholds: Calibrated threshold dictionary or StaticThresholdBaseline instance.
        ground_truth_labels: Ground-truth binary labels (True/1 for anomaly, False/0 for nominal).

    Returns:
        dict containing TP, FP, TN, FN, precision, recall, F1, and FPR.

    Raises:
        ValueError: If test_windows and ground_truth_labels lengths do not match.
    """
    if len(test_windows) != len(ground_truth_labels):
        raise ValueError(
            f"Length mismatch: {len(test_windows)} test windows but {len(ground_truth_labels)} ground-truth labels"
        )

    tp = 0
    fp = 0
    tn = 0
    fn = 0

    for window, truth in zip(test_windows, ground_truth_labels, strict=True):
        truth_bool = bool(truth)
        if isinstance(thresholds, StaticThresholdBaseline):
            opinion = thresholds.predict(window)
        else:
            opinion = run_static_threshold(window, thresholds)

        pred_anom = opinion.is_anomalous

        if pred_anom and truth_bool:
            tp += 1
        elif pred_anom and not truth_bool:
            fp += 1
        elif not pred_anom and not truth_bool:
            tn += 1
        else:
            fn += 1

    precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    f1 = (
        float((2.0 * precision * recall) / (precision + recall))
        if (precision + recall) > 0.0
        else 0.0
    )
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0

    return {
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "f1_score": f1,
        "false_positive_rate": fpr,
        "fpr": fpr,
        "total_windows": len(test_windows),
        "anomaly_count": tp + fp,
    }
