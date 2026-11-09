"""
tests.unit.test_orchestrator
============================
Unit and offline integration tests for the LangGraph orchestrator (task T3.1).

Verifies end-to-end execution across:
  TelemetryWindow
    → specialists
    → fusion engine
    → LLM reasoner
    → verifier (with retry/abstention)
    → audit log
    → final pipeline output

Owner:   Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    3 (task T3.1)
Status:  complete — end-to-end offline pipeline execution with LangGraph.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from libs.contracts import Severity, Subsystem, TelemetryWindow
from services.audit.log_writer import get_audit_entry
from services.orchestrator.graph import build_graph, run_pipeline


@pytest.fixture
def nominal_window() -> TelemetryWindow:
    t0 = datetime(2024, 1, 1, 0, 0, tzinfo=UTC)
    return TelemetryWindow(
        subsystem=Subsystem.POWER,
        start_time=t0,
        end_time=t0 + timedelta(minutes=4),
        channels={
            "P-1": [28.0] * 50,
            "P-2": [5.0] * 50,
            "T-1": [20.0] * 50,
            "A-1": [0.1] * 50,
            "C-1": [10.0] * 50,
        },
        source_dataset="SMAP",
    )


@pytest.fixture
def anomalous_window() -> TelemetryWindow:
    t0 = datetime(2024, 1, 2, 0, 0, tzinfo=UTC)
    return TelemetryWindow(
        subsystem=Subsystem.POWER,
        start_time=t0,
        end_time=t0 + timedelta(minutes=4),
        channels={
            "P-1": [55.0] * 50,  # Critical voltage spike
            "P-2": [5.0] * 50,
            "T-1": [20.0] * 50,
            "A-1": [0.1] * 50,
            "C-1": [10.0] * 50,
        },
        source_dataset="SMAP",
    )


def test_build_graph() -> None:
    compiled = build_graph()
    assert compiled is not None
    # Verify graph contains expected pipeline nodes
    assert "specialists" in compiled.nodes
    assert "fusion" in compiled.nodes
    assert "reasoner" in compiled.nodes
    assert "verifier" in compiled.nodes
    assert "audit" in compiled.nodes


def test_run_pipeline_nominal_end_to_end(
    nominal_window: TelemetryWindow,
    tmp_path: Path,
) -> None:
    db_file = tmp_path / "audit_nominal.db"
    db_url = f"sqlite:///{db_file}"

    output = run_pipeline(
        window_dict=nominal_window.model_dump(),
        run_id="run-nominal-001",
        audit_db_url=db_url,
    )

    assert "decision" in output
    assert "explanation" in output
    assert "verifier_result" in output
    assert "audit_entry" in output

    decision = output["decision"]
    assert decision.severity == Severity.NOMINAL
    assert decision.is_anomalous is False

    explanation = output["explanation"]
    assert explanation is not None
    assert explanation.cited_severity == Severity.NOMINAL

    verifier_res = output["verifier_result"]
    assert verifier_res.is_grounded is True
    assert output["abstained"] is False

    # Check audit log was written
    audit_entry = output["audit_entry"]
    assert audit_entry is not None
    persisted = get_audit_entry(audit_entry.entry_id, db_url=db_url)
    assert persisted is not None
    assert persisted.final_severity == Severity.NOMINAL
    assert persisted.abstained is False


def test_run_pipeline_anomalous_end_to_end(
    anomalous_window: TelemetryWindow,
    tmp_path: Path,
) -> None:
    db_file = tmp_path / "audit_anomalous.db"
    db_url = f"sqlite:///{db_file}"

    output = run_pipeline(
        window_dict=anomalous_window.model_dump(),
        run_id="run-anom-001",
        audit_db_url=db_url,
    )

    decision = output["decision"]
    assert decision.severity in (Severity.WARNING, Severity.CRITICAL)
    assert decision.is_anomalous is True

    explanation = output["explanation"]
    assert explanation is not None
    assert explanation.cited_severity == decision.severity
    assert "P-1" in explanation.cited_channels

    verifier_res = output["verifier_result"]
    assert verifier_res.is_grounded is True

    audit_entry = output["audit_entry"]
    assert audit_entry is not None
    assert audit_entry.final_severity == decision.severity
    assert audit_entry.abstained is False
