"""
services.orchestrator.graph
=============================
LangGraph state graph — wires all agents into the full pipeline.

Pipeline:
  TelemetryWindow
    → [specialists in parallel]
    → fuse
    → reason
    → verify (with retry / abstain)
    → audit
    → emit FusionDecision + Explanation (or evidence-only)

Owner:   Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    3 (task T3.1)
Status:  not started
"""

from __future__ import annotations

from typing import Any


def build_graph() -> Any:
    """
    Construct and return the compiled LangGraph StateGraph for Sentinel.

    Raises:
        NotImplementedError: Implementation pending task T3.1.
    """
    # TODO (T3.1): implement LangGraph skeleton with mock LLM.
    raise NotImplementedError("build_graph: implementation pending task T3.1.")


def run_pipeline(window_dict: dict[str, Any]) -> dict[str, Any]:
    """
    Run the full pipeline for a single TelemetryWindow.

    Args:
        window_dict: Serialised TelemetryWindow (from model_dump()).

    Returns:
        Pipeline output dict containing FusionDecision, VerifierResult,
        AuditEntry, and optional Explanation.

    Raises:
        NotImplementedError: Implementation pending task T3.1.
    """
    # TODO (T3.1): wire graph nodes and invoke compiled graph.
    raise NotImplementedError("run_pipeline: implementation pending task T3.1.")
