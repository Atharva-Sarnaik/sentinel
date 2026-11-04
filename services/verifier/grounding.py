"""
services.verifier.grounding
=============================
Grounding check: verifies that every claim in an Explanation
is supported by the evidence in the corresponding FusionDecision.

Design rule (ADR-0002):
  • Reject any explanation citing a channel, value or severity
    not present in the FusionDecision evidence object.
  • Max 2 retries; on third failure the system abstains
    and emits an evidence-only report.

Owner:   Sujal Hede (@Sujalhede)
Tier:    3 (task T3.3)
Status:  not started
"""

from __future__ import annotations

from libs.contracts import Explanation, FusionDecision, VerifierResult


def check_grounding(
    explanation: Explanation,
    decision: FusionDecision,
) -> VerifierResult:
    """
    Verify that all citations in explanation are grounded in decision.

    Args:
        explanation: The LLM-generated explanation to check.
        decision:    The FusionDecision used as the ground-truth evidence.

    Returns:
        VerifierResult with status GROUNDED or UNGROUNDED.

    Raises:
        NotImplementedError: Implementation pending task T3.3.
    """
    # TODO (T3.3): implement grounding verification.
    raise NotImplementedError("check_grounding: implementation pending task T3.3.")
