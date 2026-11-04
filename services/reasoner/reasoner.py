"""
services.reasoner.reasoner
============================
LLM Reasoner — produces natural-language explanations from FusionDecision evidence.

Design rule (ADR-0002):
  • The LLM explains; it does NOT decide severity.
  • Prompts are versioned files in services/reasoner/prompts/.
  • Output must conform to the Explanation JSON schema.
  • The verifier (services.verifier) checks every output for grounding.

Owner:   Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    3 (task T3.2)
Status:  not started
"""

from __future__ import annotations

from libs.contracts import Explanation, FusionDecision


def generate_explanation(
    decision: FusionDecision,
    prompt_version: str,
    llm_model: str,
) -> Explanation:
    """
    Call the LLM with a versioned prompt to explain a FusionDecision.

    Args:
        decision:       The FusionDecision produced by the fusion engine.
        prompt_version: Git tag / hash of the prompt template to use.
        llm_model:      LLM model identifier (e.g. 'gpt-4o-mini').

    Returns:
        An Explanation with structured citations for verifier grounding.

    Raises:
        NotImplementedError: Implementation pending task T3.2.
    """
    # TODO (T3.2): implement LLM call with structured output.
    raise NotImplementedError("generate_explanation: implementation pending task T3.2.")
