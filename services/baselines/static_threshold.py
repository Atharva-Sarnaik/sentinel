"""
services.baselines.static_threshold
======================================
Arm A: static per-channel threshold baseline.

Design:
  - Fixed upper bounds per channel computed from normal training telemetry.
  - If any channel reading exceeds its calibrated threshold in a window,
    an anomaly is flagged with responsible channels.
  - Outputs a frozen SpecialistOpinion contract for the ablation harness.

Owner:   Sujal Hede (@Sujalhede) / Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    1 (task T1.1)
Status:  complete — Arm A static threshold detector & calibrator.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from libs.contracts import Severity, SpecialistOpinion, TelemetryWindow


def calibrate_static_thresholds(
    windows: Sequence[TelemetryWindow],
    percentile: float = 99.0,
    min_threshold: float = 1e-4,
) -> dict[str, float]:
    """
    Calibrate static per-channel anomaly thresholds from training windows.

    Args:
        windows: Sequence of normal/healthy TelemetryWindows.
        percentile: Upper percentile (e.g. 99th) to establish the threshold boundary.
        min_threshold: Minimum floor value to prevent zero-division or zero-threshold on flat lines.

    Returns:
        dict mapping channel name to calibrated positive threshold value.
    """
    if not windows:
        return {}

    channel_values: dict[str, list[float]] = {}
    for w in windows:
        for ch, series in w.channels.items():
            if ch not in channel_values:
                channel_values[ch] = []
            channel_values[ch].extend(abs(x) for x in series)

    thresholds: dict[str, float] = {}
    for ch, vals in channel_values.items():
        if not vals:
            thresholds[ch] = min_threshold
            continue

        sorted_vals = sorted(vals)
        rank_idx = int(math.ceil((percentile / 100.0) * len(sorted_vals))) - 1
        rank_idx = max(0, min(rank_idx, len(sorted_vals) - 1))
        threshold_val = sorted_vals[rank_idx]
        thresholds[ch] = max(threshold_val, min_threshold)

    return thresholds


def run_static_threshold(
    window: TelemetryWindow,
    thresholds: dict[str, float],
    model_run_id: str = "baseline-arm-a-static",
) -> SpecialistOpinion:
    """
    Classify a TelemetryWindow using static per-channel thresholding (Arm A).

    Args:
        window: Input TelemetryWindow.
        thresholds: dict mapping channel name to threshold limit.
        model_run_id: Provenance identifier for the baseline run.

    Returns:
        SpecialistOpinion representing the baseline's assessment.
    """
    if not window.channels or not thresholds:
        return SpecialistOpinion(
            window_id=window.window_id,
            subsystem=window.subsystem,
            anomaly_score=0.0,
            severity=Severity.NOMINAL,
            responsible_channels=[],
            threshold_used=1.0,
            model_run_id=model_run_id,
        )

    responsible_channels: list[str] = []
    max_relative_violation: float = 0.0

    for ch, series in window.channels.items():
        thresh = thresholds.get(ch)
        if thresh is None or thresh <= 0.0:
            continue

        peak_val = max(abs(x) for x in series) if series else 0.0

        if peak_val > thresh:
            responsible_channels.append(ch)
            violation_ratio = (peak_val - thresh) / thresh
            if violation_ratio > max_relative_violation:
                max_relative_violation = violation_ratio

    # Compute a normalized score bounded in [0.0, 1.0]
    if not responsible_channels:
        anomaly_score = 0.0
        severity = Severity.NOMINAL
    else:
        # Logistic / tanh-like compression: score saturates to 1.0 as violation ratio grows
        anomaly_score = min(1.0, 0.5 + 0.5 * (1.0 - math.exp(-max_relative_violation)))

        # Determine severity based on number of violated channels and excess magnitude
        if len(responsible_channels) >= 2 or max_relative_violation > 1.0:
            severity = Severity.CRITICAL
        elif max_relative_violation > 0.2:
            severity = Severity.WARNING
        else:
            severity = Severity.ADVISORY

    # Effective threshold is calibrated to 0.5 anomaly score boundary
    return SpecialistOpinion(
        window_id=window.window_id,
        subsystem=window.subsystem,
        anomaly_score=anomaly_score,
        severity=severity,
        responsible_channels=responsible_channels,
        threshold_used=0.5,
        model_run_id=model_run_id,
    )
