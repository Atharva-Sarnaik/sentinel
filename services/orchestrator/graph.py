"""
services.orchestrator.graph
=============================
LangGraph state graph — wires all agents into the full Sentinel pipeline.

Pipeline:
  TelemetryWindow
    → [specialists in parallel / sequence]
    → fuse
    → reason
    → verify (with retry × 2 → abstain)
    → audit
    → emit FusionDecision + Explanation (or evidence-only)

Design rules (ADR-0002):
  • LLM never decides severity (fusion engine decides).
  • Verifier rejects ungrounded claims (max 2 retries, then abstain).
  • AuditEntry written before any outcome is returned.
  • Entire graph runs offline without external dependencies.

Owner:   Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    3 (task T3.1)
Status:  complete — compiled LangGraph StateGraph with retry, abstention, and audit logging.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from libs.common.helpers import utc_now
from libs.contracts import (
    AuditEntry,
    Explanation,
    FusionDecision,
    Severity,
    SpecialistOpinion,
    Subsystem,
    TelemetryWindow,
    VerifierResult,
    VerifierStatus,
)
from services.audit.log_writer import DEFAULT_AUDIT_DB, write_audit_entry
from services.fusion.engine import fuse
from services.observability.tracing import trace_llm_call
from services.reasoner.reasoner import DEFAULT_PROMPT_VERSION, generate_explanation
from services.verifier.grounding import check_grounding
from services.verifier.retry import MAX_RETRIES


class PipelineState(TypedDict, total=False):
    """LangGraph state schema for the Sentinel pipeline."""

    run_id: str
    window: TelemetryWindow
    opinions: list[SpecialistOpinion]
    decision: FusionDecision
    explanation: Explanation | None
    verifier_result: VerifierResult
    audit_entry: AuditEntry
    retry_count: int
    abstained: bool
    audit_db_url: str
    llm_model: str
    prompt_version: str


def specialists_node(state: PipelineState) -> dict[str, Any]:
    """
    Generate specialist opinions for the input TelemetryWindow.
    If opinions are already injected (e.g. from upstream detectors), preserve them;
    otherwise evaluate per-subsystem baseline scoring.
    """
    if state.get("opinions"):
        return {"opinions": state["opinions"]}

    window = state["window"]
    opinions: list[SpecialistOpinion] = []

    # Map available channels to subsystems
    for sub in [Subsystem.POWER, Subsystem.THERMAL, Subsystem.ATTITUDE, Subsystem.COMMUNICATIONS]:
        prefix = sub.value[0].upper()
        sub_channels = [ch for ch in window.channels if ch.startswith(prefix)]
        if not sub_channels:
            sub_channels = list(window.channels.keys())

        # Detect off-nominal readings exceeding safety threshold (> 40.0)
        resp_channels = [
            ch for ch in sub_channels if any(abs(x) > 40.0 for x in window.channels.get(ch, []))
        ]
        if resp_channels:
            score = 0.85
            sev = Severity.CRITICAL
        else:
            score = 0.05
            sev = Severity.NOMINAL

        opinions.append(
            SpecialistOpinion(
                window_id=window.window_id,
                subsystem=sub,
                anomaly_score=score,
                severity=sev,
                responsible_channels=resp_channels,
                threshold_used=0.5,
                model_run_id=f"specialist-{sub.value}-online",
                created_at=utc_now(),
            )
        )

    return {"opinions": opinions}


def fusion_node(state: PipelineState) -> dict[str, Any]:
    """Execute deterministic fusion engine on specialist opinions."""
    opinions = state["opinions"]
    decision = fuse(opinions)
    return {"decision": decision, "retry_count": 0, "abstained": False}


def reasoner_node(state: PipelineState) -> dict[str, Any]:
    """Generate structured natural-language explanation using LLM reasoner."""
    decision = state["decision"]
    llm_model = state.get("llm_model", "mock-reasoner")
    prompt_version = state.get("prompt_version", DEFAULT_PROMPT_VERSION)
    run_id = state.get("run_id", "sentinel-run-001")

    start_time = time.perf_counter()
    explanation = generate_explanation(
        decision=decision,
        prompt_version=prompt_version,
        llm_model=llm_model,
    )
    latency_ms = (time.perf_counter() - start_time) * 1000.0

    # Trace LLM call
    trace_llm_call(
        run_id=run_id,
        prompt_version=prompt_version,
        llm_model=llm_model,
        input_tokens=150,
        output_tokens=60,
        latency_ms=latency_ms,
        metadata={"decision_id": str(decision.decision_id)},
    )

    return {"explanation": explanation}


def verifier_node(state: PipelineState) -> dict[str, Any]:
    """Verify evidence grounding for the generated explanation."""
    explanation = state["explanation"]
    decision = state["decision"]
    current_retries = state.get("retry_count", 0)

    if explanation is None:
        # Already abstained
        res = VerifierResult(
            explanation_id=uuid.uuid4(),
            status=VerifierStatus.ABSTAINED,
            ungrounded_claims=["No explanation provided."],
            retry_count=current_retries,
            created_at=utc_now(),
        )
        return {"verifier_result": res, "abstained": True}

    verifier_res = check_grounding(explanation, decision, retry_count=current_retries)

    if verifier_res.is_grounded:
        return {"verifier_result": verifier_res, "abstained": False}

    # Ungrounded result
    if current_retries < MAX_RETRIES:
        return {
            "verifier_result": verifier_res,
            "retry_count": current_retries + 1,
            "abstained": False,
        }

    # Retries exhausted -> Abstain
    abstained_res = VerifierResult(
        explanation_id=explanation.explanation_id,
        status=VerifierStatus.ABSTAINED,
        ungrounded_claims=verifier_res.ungrounded_claims,
        retry_count=current_retries,
        created_at=utc_now(),
    )
    return {
        "explanation": None,
        "verifier_result": abstained_res,
        "abstained": True,
    }


def should_retry(state: PipelineState) -> str:
    """Conditional edge: check if explanation passed or needs retry."""
    verifier_res = state.get("verifier_result")
    if verifier_res is None or verifier_res.is_grounded or state.get("abstained"):
        return "audit"

    if state.get("retry_count", 0) <= MAX_RETRIES:
        return "reasoner"

    return "audit"


def audit_node(state: PipelineState) -> dict[str, Any]:
    """Persist immutable AuditEntry before returning outcomes."""
    decision = state["decision"]
    verifier_res = state["verifier_result"]
    window = state["window"]
    run_id = state.get("run_id", "sentinel-run-default")
    db_url = state.get("audit_db_url", DEFAULT_AUDIT_DB)

    entry = AuditEntry(
        run_id=run_id,
        window_id=window.window_id,
        decision_id=decision.decision_id,
        verifier_id=verifier_res.verifier_id,
        final_severity=decision.severity,
        abstained=state.get("abstained", False),
        created_at=utc_now(),
        extra={
            "fusion_rule_applied": decision.fusion_rule_applied,
            "attributed_subsystem": str(decision.attributed_subsystem)
            if decision.attributed_subsystem
            else None,
        },
    )

    write_audit_entry(entry, db_url=db_url)
    return {"audit_entry": entry}


def build_graph() -> Any:
    """
    Construct and compile the LangGraph StateGraph for the Sentinel pipeline.
    """
    workflow = StateGraph(PipelineState)

    # Add pipeline nodes
    workflow.add_node("specialists", specialists_node)
    workflow.add_node("fusion", fusion_node)
    workflow.add_node("reasoner", reasoner_node)
    workflow.add_node("verifier", verifier_node)
    workflow.add_node("audit", audit_node)

    # Set flow edges
    workflow.set_entry_point("specialists")
    workflow.add_edge("specialists", "fusion")
    workflow.add_edge("fusion", "reasoner")
    workflow.add_edge("reasoner", "verifier")

    # Conditional edge: retry loop or proceed to audit
    workflow.add_conditional_edges(
        "verifier",
        should_retry,
        {
            "reasoner": "reasoner",
            "audit": "audit",
        },
    )
    workflow.add_edge("audit", END)

    return workflow.compile()


# Cached compiled graph instance
_COMPILED_GRAPH = None


def get_compiled_graph() -> Any:
    """Retrieve or build the singleton compiled LangGraph StateGraph."""
    global _COMPILED_GRAPH
    if _COMPILED_GRAPH is None:
        _COMPILED_GRAPH = build_graph()
    return _COMPILED_GRAPH


def run_pipeline(
    window_dict: dict[str, Any],
    run_id: str = "sentinel-run-001",
    audit_db_url: str = DEFAULT_AUDIT_DB,
    llm_model: str = "mock-reasoner",
) -> dict[str, Any]:
    """
    Run the full compiled pipeline on a serialised or deserialised TelemetryWindow.

    Args:
        window_dict: TelemetryWindow data (either raw dict or model_dump()).
        run_id: Pipeline execution identifier.
        audit_db_url: Target audit database path.
        llm_model: Reasoner model name.

    Returns:
        Pipeline outcome dictionary containing:
          - decision: FusionDecision
          - explanation: Explanation | None
          - verifier_result: VerifierResult
          - audit_entry: AuditEntry
          - abstained: bool
    """
    window = (
        TelemetryWindow.model_validate(window_dict)
        if not isinstance(window_dict, TelemetryWindow)
        else window_dict
    )

    initial_state: PipelineState = {
        "run_id": run_id,
        "window": window,
        "audit_db_url": audit_db_url,
        "llm_model": llm_model,
        "prompt_version": DEFAULT_PROMPT_VERSION,
        "retry_count": 0,
        "abstained": False,
    }

    graph = get_compiled_graph()
    final_state = graph.invoke(initial_state)

    return {
        "decision": final_state.get("decision"),
        "explanation": final_state.get("explanation"),
        "verifier_result": final_state.get("verifier_result"),
        "audit_entry": final_state.get("audit_entry"),
        "abstained": final_state.get("abstained", False),
    }
