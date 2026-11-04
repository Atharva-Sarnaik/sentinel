"""
services.verifier.retry
=========================
Retry policy and abstention path for the verifier.

Policy (ADR-0002):
  • Up to 2 retries on UNGROUNDED result.
  • After 2 retries, abstain: emit evidence-only report, no explanation.

Owner:   Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    3 (task T3.4)
Status:  not started
"""

from __future__ import annotations

from libs.contracts import Explanation, FusionDecision, VerifierResult

MAX_RETRIES: int = 2  # hard limit from ADR-0002


def verify_with_retry(
    decision: FusionDecision,
    generate_fn: ...,  # type: ignore[type-arg]
    check_fn: ...,  # type: ignore[type-arg]
) -> tuple[Explanation | None, VerifierResult]:
    """
    Attempt to get a grounded explanation, retrying up to MAX_RETRIES.

    Args:
        decision:     The FusionDecision to explain.
        generate_fn:  Callable matching generate_explanation signature.
        check_fn:     Callable matching check_grounding signature.

    Returns:
        (explanation, verifier_result) where explanation is None on abstention.

    Raises:
        NotImplementedError: Implementation pending task T3.4.
    """
    # TODO (T3.4): implement retry loop with abstention path.
    raise NotImplementedError("verify_with_retry: implementation pending task T3.4.")
