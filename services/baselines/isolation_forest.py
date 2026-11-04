"""
services.baselines.isolation_forest
======================================
Arm B: Isolation Forest baseline.

Owner:   Sujal Hede (@Sujalhede)
Tier:    1 (task T1.2)
Status:  not started
"""

from __future__ import annotations

from libs.contracts import SpecialistOpinion, TelemetryWindow


def run_isolation_forest(
    window: TelemetryWindow,
    model_path: str,
) -> SpecialistOpinion:
    """
    Classify a window using a trained Isolation Forest model (arm B).

    Raises:
        NotImplementedError: Implementation pending task T1.2.
    """
    # TODO (T1.2): implement Isolation Forest baseline.
    raise NotImplementedError("run_isolation_forest: implementation pending task T1.2.")
