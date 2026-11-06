"""
tests.unit.test_manifest_and_cli
================================
Unit tests for Experiment Registry / RunManifest (T1.7) and specialists-report CLI (T1.8).

Owner:   Atharva Sarnaik (@Atharva-Sarnaik) / Sujal Hede (@Sujalhede)
Tier:    1 (tasks T1.7 & T1.8)
Status:  complete — validates manifest creation, filesystem persistence, and CLI report rendering.
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from apps.cli.main import app
from libs.common.manifest import (
    ManifestStore,
    compute_file_sha256,
    compute_sha256,
    create_run_manifest,
)

runner = CliRunner()


def test_compute_hashes(tmp_path: Path) -> None:
    text = "telemetry-channel-config-test"
    digest = compute_sha256(text)
    assert len(digest) == 64

    test_file = tmp_path / "test.txt"
    test_file.write_text(text, encoding="utf-8")
    file_digest = compute_file_sha256(test_file)
    assert file_digest == digest


def test_manifest_store_lifecycle(tmp_path: Path) -> None:
    store = ManifestStore(root_dir=tmp_path / "runs")

    manifest = create_run_manifest(
        description="Test specialists training run",
        config_data={"power": {"epochs": 10}},
        dataset_identifier="SMAP-synthetic-unit-test",
    )

    # Save
    saved_path = store.save(manifest)
    assert saved_path.is_file()

    # Get
    retrieved = store.get(manifest.run_id)
    assert retrieved is not None
    assert retrieved.run_id == manifest.run_id
    assert retrieved.description == manifest.description
    assert retrieved.config_hash == manifest.config_hash

    # List
    all_manifests = store.list_all()
    assert len(all_manifests) == 1
    assert all_manifests[0].run_id == manifest.run_id


def test_specialists_report_cli(tmp_path: Path, monkeypatch) -> None:
    # Test specialists-report with dummy run
    store = ManifestStore(root_dir=tmp_path / "runs")
    manifest = create_run_manifest(
        description="Evaluation run for Tier 1",
        config_data={"channels": ["P-1", "T-1"]},
    )
    store.save(manifest)

    # Write dummy metrics.json
    run_dir = tmp_path / "runs" / manifest.run_id
    metrics = {
        "power": {
            "channels": ["P_BUS_VOLTAGE"],
            "threshold": 0.042,
            "final_loss": 0.0015,
            "mean_anomaly_score": 0.08,
            "anomaly_count": 1,
            "n_eval": 50,
            "anomaly_rate": 0.02,
        }
    }
    (run_dir / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8")

    # Patch DEFAULT_RUNS_DIR in CLI to use tmp_path
    monkeypatch.setattr("libs.common.manifest.DEFAULT_RUNS_DIR", tmp_path / "runs")

    result = runner.invoke(app, ["specialists-report", "demo"])
    assert result.exit_code == 0
    assert "Specialist Report" in result.stdout
    assert "POWER" in result.stdout
