"""
services.fusion.engine
=========================
Deterministic fusion engine — the sole authority on severity.

Design rule (ADR-0002):
  • severity and alert level are set HERE, never by the LLM.
  • The LLM receives FusionDecision as read-only evidence.
  • Same input always produces same output (deterministic, no randomness).

Owner:   Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    2 (task T2.1)
Status:  not started
"""

from __future__ import annotations

from libs.contracts import FusionDecision, SpecialistOpinion


def fuse(opinions: list[SpecialistOpinion]) -> FusionDecision:
    """
    Fuse specialist opinions into a single FusionDecision.

    Applies severity weighting (T2.1) and cross-subsystem
    corroboration rules (T2.2).

    Args:
        opinions: List of SpecialistOpinion from all four specialists.

    Returns:
        FusionDecision with deterministically assigned severity.

    Raises:
        NotImplementedError: Implementation pending tasks T2.1–T2.4.
    """
    # TODO (T2.1 / T2.2): implement deterministic fusion.
    raise NotImplementedError("fuse: implementation pending tasks T2.1–T2.4.")
