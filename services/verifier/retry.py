"""
services.verifier.retry
=========================
Retry policy and abstention path for the verifier.

Policy (ADR-0002):
  • Up to 2 retries on UNGROUNDED result (3 total attempts).
  • After 2 retries, abstain: emit evidence-only report, no explanation.

Owner:   Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    3 (task T3.4)
Status:  complete — 2-retry loop with deterministic abstention fallback.
"""

from __future__ import annotations

import inspect
import uuid
from collections.abc import Callable

from libs.common.helpers import utc_now
from libs.contracts import Explanation, FusionDecision, VerifierResult, VerifierStatus
from services.verifier.grounding import check_grounding

MAX_RETRIES: int = 2  # Hard limit from ADR-0002


def verify_with_retry(
    decision: FusionDecision,
    generate_fn: Callable[..., Explanation],
    check_fn: Callable[..., VerifierResult] = check_grounding,
    max_retries: int = MAX_RETRIES,
) -> tuple[Explanation | None, VerifierResult]:
    """
    Attempt to get a grounded explanation, retrying up to max_retries.

    If all attempts produce ungrounded claims, the system abstains and returns
    (None, VerifierResult(status=ABSTAINED)).

    Args:
        decision: The FusionDecision ground-truth evidence.
        generate_fn: Callable generating an Explanation from FusionDecision.
        check_fn: Callable verifying grounding of Explanation against FusionDecision.
        max_retries: Maximum number of retry attempts permitted (default 2).

    Returns:
        tuple (explanation, verifier_result) where explanation is None if abstained.
    """
    last_explanation: Explanation | None = None
    last_result: VerifierResult | None = None

    for attempt in range(max_retries + 1):
        # Support generate_fn with or without retry_count argument
        try:
            sig = inspect.signature(generate_fn)
            if "retry_count" in sig.parameters or len(sig.parameters) >= 2:
                explanation = generate_fn(decision, attempt)
            else:
                explanation = generate_fn(decision)
        except TypeError:
            explanation = generate_fn(decision)

        last_explanation = explanation

        # Support check_fn with or without retry_count argument
        try:
            sig = inspect.signature(check_fn)
            if "retry_count" in sig.parameters or len(sig.parameters) >= 3:
                result = check_fn(explanation, decision, attempt)
            else:
                result = check_fn(explanation, decision)
        except TypeError:
            result = check_fn(explanation, decision)

        last_result = result

        if result.is_grounded:
            return explanation, result

    # All retries exhausted without a grounded explanation -> Abstain (ADR-0002)
    explanation_id = last_explanation.explanation_id if last_explanation else uuid.uuid4()
    ungrounded_reasons = (
        last_result.ungrounded_claims
        if last_result and last_result.ungrounded_claims
        else ["Verification failed after maximum retries."]
    )

    abstained_result = VerifierResult(
        explanation_id=explanation_id,
        status=VerifierStatus.ABSTAINED,
        ungrounded_claims=ungrounded_reasons,
        retry_count=max_retries,
        created_at=utc_now(),
    )

    return None, abstained_result
