"""
services.baselines.static_threshold
======================================
Arm A: static per-channel threshold baseline.

Owner:   Sujal Hede (@Sujalhede)
Tier:    1 (task T1.1)
Status:  not started
"""

from __future__ import annotations

from libs.contracts import SpecialistOpinion, TelemetryWindow


def run_static_threshold(
    window: TelemetryWindow,
    thresholds: dict[str, float],
) -> SpecialistOpinion:
    """
    Classify a window using fixed per-channel thresholds (arm A).

    Raises:
        NotImplementedError: Implementation pending task T1.1.
    """
    # TODO (T1.1): implement static threshold baseline.
    raise NotImplementedError("run_static_threshold: implementation pending task T1.1.")
