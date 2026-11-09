"""
tests.unit.test_audit_and_observability
=======================================
Unit tests for immutable audit logging (T3.5) and observability tracing (T3.6).

Owner:   Sujal Hede (@Sujalhede) / Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    3 (tasks T3.5 & T3.6)
Status:  complete — validates SQLite audit persistence and Langfuse tracing fallback.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from libs.common.helpers import utc_now
from libs.contracts import AuditEntry, Severity
from services.audit.log_writer import (
    get_audit_entry,
    list_audit_entries,
    write_audit_entry,
)
from services.observability.tracing import compute_cost, get_traces, trace_llm_call


def test_audit_log_write_and_query(tmp_path: Path) -> None:
    db_file = tmp_path / "test_audit.db"
    db_url = f"sqlite:///{db_file}"

    eid = uuid.uuid4()
    wid = uuid.uuid4()
    did = uuid.uuid4()
    vid = uuid.uuid4()

    entry = AuditEntry(
        entry_id=eid,
        run_id="run-test-01",
        window_id=wid,
        decision_id=did,
        verifier_id=vid,
        final_severity=Severity.WARNING,
        abstained=False,
        created_at=utc_now(),
        extra={"rule": "power_thermal_coupling"},
    )

    write_audit_entry(entry, db_url=db_url)

    # Query back
    retrieved = get_audit_entry(eid, db_url=db_url)
    assert retrieved is not None
    assert retrieved.entry_id == eid
    assert retrieved.run_id == "run-test-01"
    assert retrieved.final_severity == Severity.WARNING
    assert retrieved.abstained is False
    assert retrieved.extra["rule"] == "power_thermal_coupling"


def test_audit_log_list_filtering(tmp_path: Path) -> None:
    db_file = tmp_path / "test_audit_list.db"
    db_url = f"sqlite:///{db_file}"

    # Create entries for two different runs
    for _ in range(3):
        e = AuditEntry(
            run_id="run-alpha",
            window_id=uuid.uuid4(),
            decision_id=uuid.uuid4(),
            verifier_id=uuid.uuid4(),
            final_severity=Severity.NOMINAL,
            abstained=False,
            created_at=utc_now(),
        )
        write_audit_entry(e, db_url=db_url)

    for _ in range(2):
        e = AuditEntry(
            run_id="run-beta",
            window_id=uuid.uuid4(),
            decision_id=uuid.uuid4(),
            verifier_id=uuid.uuid4(),
            final_severity=Severity.CRITICAL,
            abstained=True,
            created_at=utc_now(),
        )
        write_audit_entry(e, db_url=db_url)

    alpha_entries = list_audit_entries(run_id="run-alpha", db_url=db_url)
    assert len(alpha_entries) == 3

    beta_entries = list_audit_entries(run_id="run-beta", db_url=db_url)
    assert len(beta_entries) == 2
    assert all(be.abstained for be in beta_entries)

    all_entries = list_audit_entries(db_url=db_url)
    assert len(all_entries) == 5


def test_observability_tracing_and_cost(tmp_path: Path) -> None:
    trace_file = tmp_path / "traces.jsonl"

    cost = compute_cost("gpt-4o-mini", input_tokens=1000, output_tokens=500)
    assert cost > 0.0

    record = trace_llm_call(
        run_id="obs-run-001",
        prompt_version="v1.0.0",
        llm_model="gpt-4o-mini",
        input_tokens=1000,
        output_tokens=500,
        latency_ms=250.5,
        metadata={"caller": "test"},
        traces_path=trace_file,
    )

    assert record["run_id"] == "obs-run-001"
    assert record["total_tokens"] == 1500
    assert record["latency_ms"] == 250.5
    assert trace_file.is_file()

    traces = get_traces(run_id="obs-run-001", traces_path=trace_file)
    assert len(traces) == 1
    assert traces[0]["llm_model"] == "gpt-4o-mini"
