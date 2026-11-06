"""
services.fusion.engine
=========================
Deterministic fusion engine — the sole authority on severity.

Design rule (ADR-0002):
  • Severity and alert level are set HERE, never by the LLM.
  • The LLM receives FusionDecision as read-only evidence.
  • Same input always produces same output (strictly deterministic).

Owner:   Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    2 (task T2.1)
Status:  complete — deterministic fusion, severity weighting, and corroboration integration.
"""

from __future__ import annotations

from libs.common.helpers import utc_now
from libs.contracts import FusionDecision, Severity, SpecialistOpinion
from services.fusion.attribution import SEVERITY_RANKS, attribute_subsystem
from services.fusion.corroboration import evaluate_corroboration_detailed


def fuse(opinions: list[SpecialistOpinion]) -> FusionDecision:
    """
    Fuse specialist opinions into a single, immutable FusionDecision.

    Applies severity weighting (T2.1), cross-subsystem corroboration rules (T2.2),
    and root-cause subsystem attribution (T2.3).

    Args:
        opinions: List of SpecialistOpinion from specialists (Power, Thermal, Attitude, Comms).

    Returns:
        FusionDecision with deterministically assigned severity.

    Raises:
        ValueError: If opinions list is empty or opinions have mismatched window IDs.
    """
    if not opinions:
        raise ValueError("Cannot fuse an empty list of opinions.")

    # Validate that all opinions correspond to the same telemetry window
    window_ids = {op.window_id for op in opinions}
    if len(window_ids) > 1:
        raise ValueError(
            f"All opinions passed to fuse() must share the same window_id, found: {window_ids}"
        )

    window_id = opinions[0].window_id

    # 1. Evaluate cross-subsystem corroboration rules
    corrob_eval = evaluate_corroboration_detailed(opinions)

    # 2. Determine root-cause attributed subsystem
    attributed = attribute_subsystem(opinions, primary_bias=corrob_eval.primary_bias)

    # 3. Compute baseline severity as the maximum specialist severity
    base_severity = Severity.NOMINAL
    for op in opinions:
        if SEVERITY_RANKS.get(op.severity, 0) > SEVERITY_RANKS.get(base_severity, 0):
            base_severity = op.severity

    # 4. Apply corroboration rule escalation if specified
    final_severity = base_severity
    if corrob_eval.escalate_to is not None:
        escalated_rank = SEVERITY_RANKS.get(corrob_eval.escalate_to, 0)
        base_rank = SEVERITY_RANKS.get(base_severity, 0)
        if escalated_rank > base_rank:
            final_severity = corrob_eval.escalate_to
        elif corrob_eval.escalate_to == Severity.NOMINAL and base_rank == 0:
            final_severity = Severity.NOMINAL

    return FusionDecision(
        window_id=window_id,
        opinions=opinions,
        severity=final_severity,
        corroborating_subsystems=corrob_eval.corroborating_subsystems,
        attributed_subsystem=attributed,
        fusion_rule_applied=corrob_eval.rule_name,
        created_at=utc_now(),
    )
