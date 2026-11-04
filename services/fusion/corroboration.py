"""
services.fusion.corroboration
================================
Cross-subsystem corroboration rules (config-driven).

Rules are loaded from channel_map.yaml / corroboration section.
Golden-case tests (T2.4) ensure the same input always fires the same rule.

Owner:   Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    2 (task T2.2)
Status:  not started
"""

from __future__ import annotations

from libs.contracts import SpecialistOpinion, Subsystem


def evaluate_corroboration(
    opinions: list[SpecialistOpinion],
) -> tuple[list[Subsystem], str]:
    """
    Evaluate cross-subsystem corroboration rules.

    Returns:
        (corroborating_subsystems, rule_label_applied)

    Raises:
        NotImplementedError: Implementation pending task T2.2.
    """
    # TODO (T2.2): implement corroboration rule evaluation.
    raise NotImplementedError("evaluate_corroboration: pending task T2.2.")
