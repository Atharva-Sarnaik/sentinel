"""
tests.unit.test_experiments
============================
Unit tests for Task T4.4 experiment execution and results generation.

Owner:   Sujal Hede (@Sujalhede)
Tier:    4 (task T4.4)
Status:  complete — validates reproducible experiment runs across all 5 arms,
         manifest persistence, metrics computation, and results documentation.
"""

from __future__ import annotations

import tempfile
from datetime import timedelta
from pathlib import Path

import pytest
from scripts.run_experiments import (
    compute_classification_metrics,
    compute_dataset_content_hash,
    generate_markdown_report,
    generate_standard_evaluation_windows,
    run_all_experiments,
)

from libs.common.manifest import ManifestStore
from libs.contracts import RunManifest, TelemetryWindow


def test_standard_evaluation_windows_determinism() -> None:
    """Verify that synthetic evaluation windows are strictly deterministic and chronological."""
    train_1, test_1, labels_1 = generate_standard_evaluation_windows(seed=42, n_train=10, n_test=5)
    train_2, test_2, labels_2 = generate_standard_evaluation_windows(seed=42, n_train=10, n_test=5)

    assert len(train_1) == 10
    assert len(test_1) == 5
    assert labels_1 == labels_2

    # Check chronological boundary: test windows must follow train windows
    assert train_1[-1].end_time < test_1[0].start_time

    # Values must be identical across identical seeds
    for w1, w2 in zip(train_1, train_2, strict=True):
        assert w1.channels == w2.channels


def test_chronological_gap_calculation() -> None:
    """Verify the exact 51-minute separation gap between training and evaluation windows."""
    train_windows, test_windows, _ = generate_standard_evaluation_windows(
        seed=42, n_train=50, n_test=30
    )
    final_train_end = train_windows[-1].end_time
    first_test_start = test_windows[0].start_time

    gap = first_test_start - final_train_end
    # t0 + 5h (300 min) - (t0 + 49*5 min + 4 min = 249 min) = 51 min
    assert gap == timedelta(minutes=51)


def test_dataset_content_hash_determinism_and_sensitivity() -> None:
    """Verify deterministic SHA-256 dataset content hashing and sensitivity to changes."""
    train_w, test_w, labels = generate_standard_evaluation_windows(seed=42, n_train=5, n_test=3)

    hash_1 = compute_dataset_content_hash(train_w, test_w, labels)
    hash_2 = compute_dataset_content_hash(train_w, test_w, labels)
    assert hash_1 == hash_2
    assert len(hash_1) == 64

    # 1. Modifying a channel value must change the hash
    modified_train = list(train_w)
    ch_mod = dict(modified_train[0].channels)
    ch_mod["P-1"] = [v + 0.01 for v in ch_mod["P-1"]]
    w_mod = TelemetryWindow(
        subsystem=modified_train[0].subsystem,
        start_time=modified_train[0].start_time,
        end_time=modified_train[0].end_time,
        channels=ch_mod,
        source_dataset=modified_train[0].source_dataset,
    )
    modified_train[0] = w_mod
    hash_mod_val = compute_dataset_content_hash(modified_train, test_w, labels)
    assert hash_mod_val != hash_1

    # 2. Modifying a ground-truth label must change the hash
    modified_labels = list(labels)
    modified_labels[0] = not modified_labels[0]
    hash_mod_label = compute_dataset_content_hash(train_w, test_w, modified_labels)
    assert hash_mod_label != hash_1

    # 3. Modifying a window timestamp must change the hash
    modified_test = list(test_w)
    w_time_mod = TelemetryWindow(
        subsystem=modified_test[0].subsystem,
        start_time=modified_test[0].start_time + timedelta(seconds=1),
        end_time=modified_test[0].end_time + timedelta(seconds=1),
        channels=modified_test[0].channels,
        source_dataset=modified_test[0].source_dataset,
    )
    modified_test[0] = w_time_mod
    hash_mod_time = compute_dataset_content_hash(train_w, modified_test, labels)
    assert hash_mod_time != hash_1


def test_classification_metrics_calculation() -> None:
    """Verify precision, recall, F1, and FPR metrics calculation."""
    preds = [True, True, False, False]
    truth = [True, False, False, True]

    metrics = compute_classification_metrics(preds, truth)
    assert metrics["true_positives"] == 1
    assert metrics["false_positives"] == 1
    assert metrics["true_negatives"] == 1
    assert metrics["false_negatives"] == 1
    assert metrics["precision"] == 0.5
    assert metrics["recall"] == 0.5
    assert metrics["f1"] == 0.5
    assert metrics["false_positive_rate"] == 0.5


def test_classification_metrics_validation_and_empty() -> None:
    """Verify input validation: length mismatch raises ValueError, empty input is zeroed."""
    # Length mismatch
    with pytest.raises(ValueError, match="Length mismatch"):
        compute_classification_metrics([True, False], [True])

    # Empty inputs
    metrics = compute_classification_metrics([], [])
    assert metrics["true_positives"] == 0
    assert metrics["false_positives"] == 0
    assert metrics["true_negatives"] == 0
    assert metrics["false_negatives"] == 0
    assert metrics["precision"] == 0.0
    assert metrics["recall"] == 0.0
    assert metrics["f1"] == 0.0
    assert metrics["false_positive_rate"] == 0.0


def test_classification_metrics_zero_division() -> None:
    """Verify safe zero-division handling when no positive predictions/labels exist."""
    preds = [False, False]
    truth = [False, False]
    metrics = compute_classification_metrics(preds, truth)
    assert metrics["precision"] == 0.0
    assert metrics["recall"] == 0.0
    assert metrics["f1"] == 0.0
    assert metrics["false_positive_rate"] == 0.0


def test_experiment_runs_and_manifest_storage() -> None:
    """Verify that run_all_experiments executes all 5 arms and persists valid RunManifests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        results = run_all_experiments(seed=99, output_runs_dir=tmp_dir)

        assert "Arm_A" in results
        assert "Arm_B" in results
        assert "Arm_C" in results
        assert "Arm_D" in results
        assert "Arm_E" in results
        assert "T4.3_Golden_Set" in results

        # Verify Arm E executed and has a valid model_run_id
        assert results["Arm_E"]["model_run_id"] == "exp-arm-e-sentinel-99"
        assert results["Arm_E"]["status"] == "EXECUTED"
        assert "event_f1" in results["Arm_E"]

        # Verify manifest persistence for all 5 arms: Arms A, B, C, D, E
        store = ManifestStore(root_dir=tmp_dir)
        all_manifests = store.list_all()
        assert len(all_manifests) == 5

        run_ids = {m.run_id for m in all_manifests}
        assert "exp-arm-a-static-99" in run_ids
        assert "exp-arm-b-iforest-99" in run_ids
        assert "exp-arm-c-combined-lstm-ae-99" in run_ids
        assert "exp-arm-d-specialists-99" in run_ids
        assert "exp-arm-e-sentinel-99" in run_ids

        for manifest in all_manifests:
            assert isinstance(manifest, RunManifest)
            assert len(manifest.config_hash) == 64
            assert len(manifest.dataset_dvc_hash) == 64
            # Verify MLflow metadata honesty
            assert manifest.mlflow_run_ids == {}
            assert manifest.mlflow_experiment_id == "offline"


def test_markdown_report_generation() -> None:
    """Verify that results_tables markdown document is generated with required sections."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        report_file = Path(tmp_dir) / "test_results.md"
        results = run_all_experiments(seed=42, output_runs_dir=tmp_dir)
        generate_markdown_report(results, report_file)

        assert report_file.is_file()
        content = report_file.read_text(encoding="utf-8")

        # Verify required sections
        assert "Comparative Results Across Experimental Arms" in content
        assert "Headline Event-Wise Metrics" in content
        assert "Results Interpretation & Architectural Analysis" in content
        assert "Arm D: Per-Subsystem Specialist Performance" in content
        assert "T4.3 Explanation Grounding Benchmark Status" in content
        assert "Reproduction Commands" in content
        assert "Synthetic-Standard-Verification" in content
        assert "51 minutes" in content
        assert "exp-arm-a-static-42" in content
        assert "exp-arm-e-sentinel-42" in content
