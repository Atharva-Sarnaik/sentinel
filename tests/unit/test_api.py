"""
tests.unit.test_api
===================
Unit tests for Task T5.2: Sentinel FastAPI Web Service (services.api.app).

Tests:
  - GET /health: Service status endpoint.
  - POST /analyze: End-to-end multi-agent pipeline invocation with valid payload.
  - POST /analyze: Input validation and rejection (422 Unprocessable Entity).
  - GET /runs: List experiment manifests.
  - GET /runs/{run_id}: Retrieve manifest and metrics (success and 404 cases).
  - GET /audit/{entry_id}: UUID validation (400), missing entry (404), and retrieval (200).

Owner:   Sujal Hede (@Sujalhede)
Tier:    5 (task T5.2)
"""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from libs.common.helpers import utc_now
from libs.common.manifest import ManifestStore, create_run_manifest
from libs.contracts import AuditEntry, Severity
from services.api.app import app
from services.audit.log_writer import write_audit_entry

client = TestClient(app)


def test_health_check() -> None:
    """Verify /health returns 200 OK and expected system metadata."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Sentinel API"
    assert data["tier"] == "5"


def test_analyze_endpoint_success() -> None:
    """Verify POST /analyze executes multi-agent pipeline and returns complete outcome."""
    payload = {
        "subsystem": "power",
        "start_time": "2024-01-01T00:00:00Z",
        "end_time": "2024-01-01T00:04:00Z",
        "channels": {
            "P-1": [28.0, 28.1, 48.5, 49.0],
            "T-1": [45.0, 45.2, 72.0, 75.0],
            "A-1": [1.0, 1.0, 1.0, 1.0],
            "C-1": [5.0, 5.0, 5.0, 5.0],
        },
        "source_dataset": "Unit-Test-API",
    }
    resp = client.post("/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert "decision" in data
    assert "explanation" in data
    assert "verifier_result" in data
    assert "audit_entry" in data
    assert "abstained" in data

    decision = data["decision"]
    assert "severity" in decision
    assert decision["severity"] in ["nominal", "warning", "critical"]
    assert "corroborating_subsystems" in decision


def test_analyze_endpoint_validation_error() -> None:
    """Verify POST /analyze rejects malformed telemetry payloads with 422."""
    bad_payload = {
        "subsystem": "invalid_subsystem",
        "channels": "not_a_dict",
    }
    resp = client.post("/analyze", json=bad_payload)
    assert resp.status_code == 422


def test_list_runs_endpoint() -> None:
    """Verify GET /runs returns a list of run records."""
    resp = client.get("/runs")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


def test_get_run_manifest_success_and_not_found(tmp_path: Path, monkeypatch) -> None:
    """Verify GET /runs/{run_id} returns 200 on existing run and 404 on missing run."""
    store = ManifestStore(root_dir=tmp_path / "runs")
    manifest = create_run_manifest(
        description="API unit test run",
        config_data={"test": True},
        dataset_identifier="test-ds",
    )
    store.save(manifest)

    # Override get_manifest_store in the services.api.app module
    import sys

    api_app_mod = sys.modules["services.api.app"]
    monkeypatch.setattr(api_app_mod, "get_manifest_store", lambda: store)

    # Test existing run
    resp = client.get(f"/runs/{manifest.run_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["manifest"]["run_id"] == manifest.run_id

    # Test 404 for missing run
    missing_resp = client.get("/runs/non_existent_run_99999")
    assert missing_resp.status_code == 404
    assert "not found" in missing_resp.json()["detail"].lower()


def test_get_audit_entry_success_and_errors() -> None:
    """Verify GET /audit/{entry_id} retrieves audit entry and handles invalid/missing UUIDs."""
    # 1. Invalid UUID -> 400 Bad Request
    resp_bad = client.get("/audit/not-a-valid-uuid")
    assert resp_bad.status_code == 400
    assert "invalid uuid format" in resp_bad.json()["detail"].lower()

    # 2. Non-existent UUID -> 404 Not Found
    random_id = str(uuid.uuid4())
    resp_missing = client.get(f"/audit/{random_id}")
    assert resp_missing.status_code == 404

    # 3. Existing audit entry -> 200 OK
    entry = AuditEntry(
        run_id="api-test-run",
        window_id=uuid.uuid4(),
        decision_id=uuid.uuid4(),
        verifier_id=uuid.uuid4(),
        final_severity=Severity.WARNING,
        abstained=False,
        created_at=utc_now(),
        extra={"test_key": "test_val"},
    )
    # Write to default audit db
    write_audit_entry(entry)

    resp_found = client.get(f"/audit/{entry.entry_id}")
    assert resp_found.status_code == 200
    data = resp_found.json()
    assert data["entry_id"] == str(entry.entry_id)
    assert data["run_id"] == "api-test-run"
    assert data["final_severity"] == "warning"
