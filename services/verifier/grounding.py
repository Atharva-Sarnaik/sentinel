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

Owner:   Sujal Hede (@Sujalhede) / Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    3 (task T3.3)
Status:  complete — strict evidence grounding validation for channel citations and severity.
"""

from __future__ import annotations

from libs.common.helpers import utc_now
from libs.contracts import Explanation, FusionDecision, VerifierResult, VerifierStatus


def check_grounding(
    explanation: Explanation,
    decision: FusionDecision,
    retry_count: int = 0,
) -> VerifierResult:
    """
    Verify that all citations in explanation are grounded in decision evidence.

    Checks:
      1. Explanation links to the correct decision_id.
      2. Cited severity strictly matches FusionDecision.severity (no escalation/de-escalation).
      3. All cited channels are present in the evidence object (either responsible channels
         or recognized channels within the specialist opinions).

    Args:
        explanation: The LLM-generated explanation to verify.
        decision: The FusionDecision ground-truth evidence.
        retry_count: Current retry iteration index (0 <= retry_count <= 2).

    Returns:
        VerifierResult with status GROUNDED or UNGROUNDED.
    """
    ungrounded_claims: list[str] = []

    # 1. Decision ID cross-reference check
    if explanation.decision_id != decision.decision_id:
        ungrounded_claims.append(
            f"Explanation decision_id ({explanation.decision_id}) does not match "
            f"FusionDecision decision_id ({decision.decision_id})."
        )

    # 2. Strict severity grounding check (ADR-0002)
    if explanation.cited_severity != decision.severity:
        ungrounded_claims.append(
            f"Severity mismatch: explanation cited '{explanation.cited_severity.value}', "
            f"but fused decision severity is '{decision.severity.value}'."
        )

    # 3. Channel citations grounding check (ADR-0002)
    # Collect all legitimate channel names present in the evidence
    evidence_channels: set[str] = set()
    for op in decision.opinions:
        evidence_channels.update(op.responsible_channels)

    for ch in explanation.cited_channels:
        if ch not in evidence_channels:
            ungrounded_claims.append(
                f"Ungrounded channel citation: channel '{ch}' is not present in the evidence."
            )

    # Determine status
    status = VerifierStatus.GROUNDED if not ungrounded_claims else VerifierStatus.UNGROUNDED
    clamped_retry_count = max(0, min(retry_count, 2))

    return VerifierResult(
        explanation_id=explanation.explanation_id,
        status=status,
        ungrounded_claims=ungrounded_claims,
        retry_count=clamped_retry_count,
        created_at=utc_now(),
    )
