"""
services.fusion.attribution
=============================
Subsystem attribution logic for identifying the root-cause subsystem (task T2.3).

Determines which subsystem is the primary source of the observed telemetry anomaly.

Owner:   Sujal Hede (@Sujalhede) / Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    2 (task T2.3)
Status:  complete — deterministic root-cause attribution logic.
"""

from __future__ import annotations

from libs.contracts import Severity, SpecialistOpinion, Subsystem

# Severity priority ranking for comparison
SEVERITY_RANKS: dict[Severity, int] = {
    Severity.NOMINAL: 0,
    Severity.ADVISORY: 1,
    Severity.WARNING: 2,
    Severity.CRITICAL: 3,
}

# Deterministic tie-breaker priority order for equal anomaly scores
SUBSYSTEM_PRIORITY: list[Subsystem] = [
    Subsystem.POWER,
    Subsystem.ATTITUDE,
    Subsystem.THERMAL,
    Subsystem.COMMUNICATIONS,
]


def attribute_subsystem(
    opinions: list[SpecialistOpinion],
    primary_bias: Subsystem | None = None,
) -> Subsystem | None:
    """
    Attribute an anomaly to its primary root-cause subsystem.

    Args:
        opinions: List of SpecialistOpinion instances across subsystems.
        primary_bias: Optional subsystem bias suggested by physics coupling rule.

    Returns:
        The Subsystem attributed as the root cause, or None if nominal.
    """
    if not opinions:
        return None

    # Filter to active anomalous opinions
    anomalous_opinions = [op for op in opinions if op.is_anomalous]

    if not anomalous_opinions:
        return None

    anomalous_subsystems = {op.subsystem for op in anomalous_opinions}

    # If the corroboration rule has a specific physical root-cause bias (e.g. attitude -> comms)
    # and that subsystem is among the anomalous set, prioritize it.
    if primary_bias is not None and primary_bias in anomalous_subsystems:
        return primary_bias

    # Otherwise sort deterministically:
    # 1. Severity rank (CRITICAL > WARNING > ADVISORY)
    # 2. Anomaly score (higher score first)
    # 3. Number of responsible channels (more channels first)
    # 4. Fixed subsystem priority index (lower index first)
    def sort_key(op: SpecialistOpinion) -> tuple[int, float, int, int]:
        sev_rank = SEVERITY_RANKS.get(op.severity, 0)
        score = op.anomaly_score
        n_channels = len(op.responsible_channels)
        try:
            prio_idx = -SUBSYSTEM_PRIORITY.index(op.subsystem)
        except ValueError:
            prio_idx = -99
        return (sev_rank, score, n_channels, prio_idx)

    best_opinion = max(anomalous_opinions, key=sort_key)
    return best_opinion.subsystem
