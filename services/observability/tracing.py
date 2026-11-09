"""
services.observability.tracing
================================
Langfuse tracing, cost tracking, and latency logging for LLM calls (task T3.6).

Provides structured trace persistence with local JSONL fallback when Langfuse
cloud credentials are not configured (offline CI / test mode).

Owner:   Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    3 (task T3.6)
Status:  complete — Langfuse cloud integration with local JSONL audit fallback and cost calculation.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_TRACES_PATH = Path("artifacts/traces.jsonl")

# Standard token cost estimations ($ per token)
MODEL_PRICING: dict[str, tuple[float, float]] = {
    # (input_cost_per_token, output_cost_per_token)
    "gpt-4o-mini": (0.15 / 1_000_000, 0.60 / 1_000_000),
    "gpt-4o": (2.50 / 1_000_000, 10.00 / 1_000_000),
    "mock-reasoner": (0.0, 0.0),
}


def compute_cost(llm_model: str, input_tokens: int, output_tokens: int) -> float:
    """Compute estimated USD cost for token usage."""
    input_rate, output_rate = MODEL_PRICING.get(llm_model, (0.0, 0.0))
    return float(input_tokens * input_rate + output_tokens * output_rate)


def trace_llm_call(
    run_id: str,
    prompt_version: str,
    llm_model: str,
    input_tokens: int,
    output_tokens: int,
    latency_ms: float,
    metadata: dict[str, Any] | None = None,
    traces_path: Path | str = DEFAULT_TRACES_PATH,
) -> dict[str, Any]:
    """
    Log a single LLM call to Langfuse or local JSONL trace store.

    Args:
        run_id: Sentinel run identifier.
        prompt_version: Prompt template version used.
        llm_model: Model identifier.
        input_tokens: Number of input tokens.
        output_tokens: Number of output tokens.
        latency_ms: Wall-clock latency in milliseconds.
        metadata: Optional extra metadata.
        traces_path: Path to local JSONL trace fallback.

    Returns:
        Structured trace record dict.
    """
    cost_usd = compute_cost(llm_model, input_tokens, output_tokens)
    trace_record: dict[str, Any] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "run_id": run_id,
        "prompt_version": prompt_version,
        "llm_model": llm_model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "latency_ms": latency_ms,
        "estimated_cost_usd": cost_usd,
        "metadata": metadata or {},
    }

    # If Langfuse credentials are present, attempt live trace
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    if public_key and secret_key:
        try:
            from langfuse import Langfuse

            langfuse = Langfuse(public_key=public_key, secret_key=secret_key)
            langfuse.trace(
                name="sentinel-llm-reasoner",
                user_id=run_id,
                metadata=trace_record,
            )
        except Exception:
            pass  # Fall back gracefully to local recording

    # Always persist locally to JSONL
    dest = Path(traces_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "a", encoding="utf-8") as f:
        f.write(json.dumps(trace_record) + "\n")

    return trace_record


def get_traces(
    run_id: str | None = None,
    traces_path: Path | str = DEFAULT_TRACES_PATH,
) -> list[dict[str, Any]]:
    """Retrieve logged traces from local JSONL store."""
    dest = Path(traces_path)
    if not dest.is_file():
        return []

    records: list[dict[str, Any]] = []
    with open(dest, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    data = json.loads(line)
                    if run_id is None or data.get("run_id") == run_id:
                        records.append(data)
                except Exception:
                    continue
    return records
