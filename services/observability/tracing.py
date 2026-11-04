"""
services.observability.tracing
================================
Langfuse tracing, cost tracking, and latency logging for LLM calls.

Owner:   Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    3 (task T3.6)
Status:  not started
"""

from __future__ import annotations

from typing import Any


def trace_llm_call(
    run_id: str,
    prompt_version: str,
    llm_model: str,
    input_tokens: int,
    output_tokens: int,
    latency_ms: float,
    metadata: dict[str, Any] | None = None,
) -> None:
    """
    Log a single LLM call to Langfuse.

    Args:
        run_id:        Sentinel run identifier.
        prompt_version: Prompt template version used.
        llm_model:     Model identifier.
        input_tokens:  Number of input tokens.
        output_tokens: Number of output tokens.
        latency_ms:    Wall-clock latency in milliseconds.
        metadata:      Optional extra metadata.

    Raises:
        NotImplementedError: Implementation pending task T3.6.
    """
    # TODO (T3.6): implement Langfuse tracing.
    raise NotImplementedError("trace_llm_call: implementation pending task T3.6.")
