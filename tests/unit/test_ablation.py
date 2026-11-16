"""
tests.unit.test_ablation
==========================
Unit tests for Task T4.2: Ablation Study Runner (services.evaluation.ablation).

Owner:   Atharva Sarnaik (@Atharva-Sarnaik) / Sujal Hede (@Sujalhede)
Tier:    4 (task T4.2)
Status:  complete — validates arm subsetting, identical window consistency,
         dependency injection, honest Arm E blocker reporting, and metrics.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock

import pytest

from libs.contracts import (
    FusionDecision,
    Severity,
    SpecialistOpinion,
    Subsystem,
    TelemetryWindow,
)
from services.evaluation.ablation import ARMS, compute_binary_metrics, run_ablation


def _make_dummy_window(
    offset_min: int = 0,
    values: dict[str, list[float]] | None = None,
) -> TelemetryWindow:
    t0 = datetime(2024, 1, 1, 0, 0, tzinfo=UTC) + timedelta(minutes=offset_min)
    ch = values or {
        "P-1": [28.0] * 10,
        "T-1": [45.0] * 10,
        "A-1": [1.0] * 10,
        "C-1": [5.0] * 10,
    }
    return TelemetryWindow(
        window_id=uuid.uuid4(),
        subsystem=Subsystem.POWER,
        start_time=t0,
        end_time=t0 + timedelta(minutes=4),
        channels=ch,
        source_dataset="Synthetic-Standard-Verification",
    )


def test_input_validation_empty_windows() -> None:
    """Verify run_ablation rejects an empty windows sequence with ValueError."""
    with pytest.raises(ValueError, match="Cannot run ablation on empty windows sequence"):
        run_ablation([])


def test_input_validation_empty_arms() -> None:
    """Verify run_ablation rejects an empty arms tuple with ValueError and checks ARMS constant."""
    assert ARMS == ("A", "B", "C", "D", "E")
    w = _make_dummy_window()
    with pytest.raises(ValueError, match="arms tuple must not be empty"):
        run_ablation([w], arms=())


def test_input_validation_invalid_arm() -> None:
    """Verify run_ablation rejects unrecognized arm identifiers."""
    w = _make_dummy_window()
    with pytest.raises(ValueError, match="Unrecognized ablation arm 'Z'"):
        run_ablation([w], arms=("A", "Z"))


def test_input_validation_ground_truth_mismatch() -> None:
    """Verify run_ablation rejects ground_truth of mismatched length."""
    w1 = _make_dummy_window(0)
    w2 = _make_dummy_window(5)
    with pytest.raises(ValueError, match="Length mismatch: ground_truth"):
        run_ablation([w1, w2], arms=("A",), ground_truth=[True])


def test_compute_binary_metrics_edge_cases() -> None:
    """Verify binary classification metrics helper calculation and edge cases."""
    # Length mismatch
    with pytest.raises(ValueError, match="Length mismatch"):
        compute_binary_metrics([True], [True, False])

    # Empty inputs
    empty_res = compute_binary_metrics([], [])
    assert empty_res["true_positives"] == 0
    assert empty_res["precision"] == 0.0
    assert empty_res["recall"] == 0.0

    # Normal case
    res = compute_binary_metrics([True, True, False, False], [True, False, False, True])
    assert res["true_positives"] == 1
    assert res["false_positives"] == 1
    assert res["true_negatives"] == 1
    assert res["false_negatives"] == 1
    assert res["precision"] == 0.5
    assert res["recall"] == 0.5
    assert res["f1"] == 0.5
    assert res["false_positive_rate"] == 0.5


def test_run_ablation_arm_subsetting_and_mock_injection() -> None:
    """Verify running a subset of arms with injected mock models."""
    windows = [_make_dummy_window(i * 5) for i in range(4)]
    ground_truth = [True, False, True, False]

    # Create mock detectors that return SpecialistOpinion
    def make_mock(pred_flags: list[bool]) -> Any:
        mock = MagicMock()
        mock.predict.side_effect = [
            SpecialistOpinion(
                window_id=w.window_id,
                subsystem=Subsystem.POWER,
                anomaly_score=0.9 if flag else 0.1,
                severity=Severity.CRITICAL if flag else Severity.NOMINAL,
                threshold_used=0.5,
                model_run_id="run-mock-a",
            )
            for w, flag in zip(windows, pred_flags, strict=True)
        ]
        return mock

    mock_a = make_mock([True, False, True, False])  # Perfect match
    mock_b = make_mock([True, True, True, True])  # High false positives

    results = run_ablation(
        windows=windows,
        arms=("A", "B"),
        ground_truth=ground_truth,
        models={"A": mock_a, "B": mock_b},
    )

    # Subsetting verification
    assert set(results.keys()) == {"A", "B"}
    assert "C" not in results
    assert "D" not in results
    assert "E" not in results

    # Arm A metrics
    assert results["A"]["precision"] == 1.0
    assert results["A"]["recall"] == 1.0
    assert results["A"]["f1"] == 1.0
    assert results["A"]["false_positive_rate"] == 0.0

    # Arm B metrics
    assert results["B"]["precision"] == 0.5
    assert results["B"]["recall"] == 1.0
    assert results["B"]["false_positive_rate"] == 1.0


def test_run_ablation_identical_windows_consistency() -> None:
    """Verify that all arms evaluate on identical windows in exact sequence."""
    windows = [_make_dummy_window(i * 5) for i in range(3)]
    captured_windows_a: list[uuid.UUID] = []
    captured_windows_b: list[uuid.UUID] = []

    mock_a = MagicMock()
    mock_b = MagicMock()

    def record_a(w: TelemetryWindow) -> SpecialistOpinion:
        captured_windows_a.append(w.window_id)
        return SpecialistOpinion(
            window_id=w.window_id,
            subsystem=Subsystem.POWER,
            anomaly_score=0.1,
            severity=Severity.NOMINAL,
            threshold_used=0.5,
            model_run_id="run-mock-a",
        )

    def record_b(w: TelemetryWindow) -> SpecialistOpinion:
        captured_windows_b.append(w.window_id)
        return SpecialistOpinion(
            window_id=w.window_id,
            subsystem=Subsystem.POWER,
            anomaly_score=0.1,
            severity=Severity.NOMINAL,
            threshold_used=0.5,
            model_run_id="run-mock-b",
        )

    mock_a.predict.side_effect = record_a
    mock_b.predict.side_effect = record_b

    run_ablation(
        windows=windows,
        arms=("A", "B"),
        models={"A": mock_a, "B": mock_b},
    )

    expected_ids = [w.window_id for w in windows]
    assert captured_windows_a == expected_ids
    assert captured_windows_b == expected_ids


def test_run_ablation_arm_d_independent_specialists() -> None:
    """Verify Arm D evaluates multiple specialists independently and unions window decisions."""
    windows = [_make_dummy_window(i * 5) for i in range(3)]
    ground_truth = [True, True, False]

    # Specialist 1 flags window 0
    spec_power = MagicMock()
    spec_power.analyze.side_effect = [
        SpecialistOpinion(
            window_id=windows[0].window_id,
            subsystem=Subsystem.POWER,
            anomaly_score=0.8,
            severity=Severity.WARNING,
            threshold_used=0.5,
            model_run_id="run-power",
        ),
        SpecialistOpinion(
            window_id=windows[1].window_id,
            subsystem=Subsystem.POWER,
            anomaly_score=0.1,
            severity=Severity.NOMINAL,
            threshold_used=0.5,
            model_run_id="run-power",
        ),
        SpecialistOpinion(
            window_id=windows[2].window_id,
            subsystem=Subsystem.POWER,
            anomaly_score=0.1,
            severity=Severity.NOMINAL,
            threshold_used=0.5,
            model_run_id="run-power",
        ),
    ]

    # Specialist 2 flags window 1
    spec_thermal = MagicMock()
    spec_thermal.analyze.side_effect = [
        SpecialistOpinion(
            window_id=windows[0].window_id,
            subsystem=Subsystem.THERMAL,
            anomaly_score=0.1,
            severity=Severity.NOMINAL,
            threshold_used=0.5,
            model_run_id="run-thermal",
        ),
        SpecialistOpinion(
            window_id=windows[1].window_id,
            subsystem=Subsystem.THERMAL,
            anomaly_score=0.8,
            severity=Severity.WARNING,
            threshold_used=0.5,
            model_run_id="run-thermal",
        ),
        SpecialistOpinion(
            window_id=windows[2].window_id,
            subsystem=Subsystem.THERMAL,
            anomaly_score=0.1,
            severity=Severity.NOMINAL,
            threshold_used=0.5,
            model_run_id="run-thermal",
        ),
    ]

    def make_nom_spec(sub: Subsystem) -> MagicMock:
        m = MagicMock()
        m.analyze.return_value = SpecialistOpinion(
            window_id=windows[0].window_id,
            subsystem=sub,
            anomaly_score=0.1,
            severity=Severity.NOMINAL,
            threshold_used=0.5,
            model_run_id=f"run-{sub.value}",
        )
        return m

    models_d = {
        "power": spec_power,
        "thermal": spec_thermal,
        "attitude": make_nom_spec(Subsystem.ATTITUDE),
        "communications": make_nom_spec(Subsystem.COMMUNICATIONS),
    }

    results = run_ablation(
        windows=windows,
        arms=("D",),
        ground_truth=ground_truth,
        models={"D": models_d},
    )

    assert "D" in results
    res_d = results["D"]
    assert res_d["anomaly_count"] == 2  # windows 0 and 1 unioned
    assert res_d["precision"] == 1.0
    assert res_d["recall"] == 1.0
    assert res_d["f1"] == 1.0
    assert res_d["per_subsystem_anomaly_counts"]["power"] == 1
    assert res_d["per_subsystem_anomaly_counts"]["thermal"] == 1


def test_run_ablation_arm_e_blocked_graceful(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify Arm E cleanly reports BLOCKED_PENDING_TIER_3 when Tier 3 raises NotImplementedError."""

    def mock_not_implemented(*args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError("run_pipeline: implementation pending task T3.1.")

    monkeypatch.setattr("services.orchestrator.graph.run_pipeline", mock_not_implemented)
    windows = [_make_dummy_window(0)]
    results = run_ablation(windows=windows, arms=("E",))

    assert "E" in results
    arm_e = results["E"]
    assert arm_e["status"] == "BLOCKED_PENDING_TIER_3"
    assert len(arm_e["blockers"]) >= 4
    assert any("services.orchestrator.graph" in b for b in arm_e["blockers"])


def test_run_ablation_arm_e_injected_pipeline() -> None:
    """Verify Arm E executes and computes metrics when a valid pipeline callable is injected."""
    windows = [_make_dummy_window(i * 5) for i in range(2)]
    ground_truth = [True, False]

    # Mock pipeline callable returning simulated orchestrator output dict
    def mock_pipeline(w: TelemetryWindow) -> dict[str, Any]:
        is_anom = w.start_time.minute == 0
        return {
            "window_id": w.window_id,
            "decision": MagicMock(is_anomalous=is_anom),
            "severity": Severity.CRITICAL if is_anom else Severity.NOMINAL,
        }

    results = run_ablation(
        windows=windows,
        arms=("E",),
        ground_truth=ground_truth,
        pipeline_fn=mock_pipeline,
    )

    assert "E" in results
    arm_e = results["E"]
    assert arm_e["status"] == "EXECUTED_WITH_INJECTED_PIPELINE"
    assert arm_e["anomaly_count"] == 1
    assert arm_e["precision"] == 1.0
    assert arm_e["recall"] == 1.0


def test_strict_train_eval_separation_enforced() -> None:
    """Verify that unfitted models without train_windows raise ValueError to prevent leakage."""
    windows = [_make_dummy_window(0)]

    # Arm A without models or train_windows
    with pytest.raises(ValueError, match="Arm A requires either a pre-fitted model"):
        run_ablation(windows=windows, arms=("A",))

    # Arm B without models or train_windows
    with pytest.raises(ValueError, match="Arm B requires either a pre-fitted model"):
        run_ablation(windows=windows, arms=("B",))

    # Arm C without models or train_windows
    with pytest.raises(ValueError, match="Arm C requires either a pre-trained detector"):
        run_ablation(windows=windows, arms=("C",))

    # Arm D without models or train_windows
    with pytest.raises(ValueError, match="Arm D requires either pre-trained specialists"):
        run_ablation(windows=windows, arms=("D",))


def test_run_ablation_end_to_end_with_train_windows() -> None:
    """Verify end-to-end execution of Arm A with separate train_windows."""
    train_windows = [_make_dummy_window(i * 5) for i in range(10)]
    test_windows = [_make_dummy_window(100 + i * 5) for i in range(5)]
    ground_truth = [False] * 5

    results = run_ablation(
        windows=test_windows,
        arms=("A",),
        ground_truth=ground_truth,
        train_windows=train_windows,
    )

    assert "A" in results
    assert results["A"]["sample_count"] == 5
    assert results["A"]["precision"] == 0.0 or results["A"]["f1"] == 0.0
    assert results["A"]["false_positive_rate"] == 0.0


def test_run_ablation_arm_d_all_four_specialists() -> None:
    """Verify Arm D executes all 4 specialists (Power, Thermal, Attitude, Comms) and unions decisions."""
    windows = [_make_dummy_window(i * 5) for i in range(4)]
    subsystems = [
        Subsystem.POWER,
        Subsystem.THERMAL,
        Subsystem.ATTITUDE,
        Subsystem.COMMUNICATIONS,
    ]

    models_d: dict[str, Any] = {}
    for i, sub in enumerate(subsystems):
        mock_spec = MagicMock()
        mock_spec.subsystem = sub
        # Each specialist i flags window i only
        mock_spec.analyze.side_effect = [
            SpecialistOpinion(
                window_id=w.window_id,
                subsystem=sub,
                anomaly_score=0.9 if j == i else 0.1,
                severity=Severity.CRITICAL if j == i else Severity.NOMINAL,
                threshold_used=0.5,
                model_run_id=f"run-{sub.value}",
            )
            for j, w in enumerate(windows)
        ]
        models_d[sub.value] = mock_spec

    results = run_ablation(
        windows=windows,
        arms=("D",),
        models={"D": models_d},
    )

    assert "D" in results
    res_d = results["D"]
    assert res_d["status"] == "EXECUTED"
    assert set(res_d["subsystems_evaluated"]) == {
        "power",
        "thermal",
        "attitude",
        "communications",
    }
    for sub in ["power", "thermal", "attitude", "communications"]:
        assert res_d["per_subsystem_anomaly_counts"][sub] == 1
    # Each window was flagged by exactly one specialist; union yields all 4 anomalous
    assert res_d["anomaly_count"] == 4
    assert res_d["anomaly_rate"] == 1.0


def test_run_ablation_arm_d_rejects_summary_dictionaries() -> None:
    """Verify Arm D proves summary metrics dictionaries cannot silently become all-false predictions."""
    windows = [_make_dummy_window(i * 5) for i in range(3)]
    # Summary metrics dictionary simulating train_all_from_configs() output
    summary_dict = {
        "power": {
            "n_train": 10,
            "n_eval": 10,
            "anomaly_rate": 0.1,
            "final_loss": 0.05,
        },
        "thermal": {
            "n_train": 10,
            "n_eval": 10,
            "anomaly_rate": 0.0,
            "final_loss": 0.02,
        },
    }

    results = run_ablation(
        windows=windows,
        arms=("D",),
        ground_truth=[True, False, True],
        models={"D": summary_dict},
    )

    assert "D" in results
    res_d = results["D"]
    # Must report UNAVAILABLE and must NEVER fabricate all-false predictions or f1/precision metrics
    assert res_d["status"] == "UNAVAILABLE"
    assert "anomaly_count" not in res_d
    assert "predictions" not in res_d
    assert "precision" not in res_d
    assert "f1" not in res_d
    assert res_d["sample_count"] == 3
    assert (
        "summary metrics" in res_d["reason"].lower() or "summary metrics" in res_d["error"].lower()
    )


def test_run_ablation_arm_d_per_window_predictions_and_metrics() -> None:
    """Verify Arm D calculates exact per-window predictions and per-subsystem metrics."""
    windows = [_make_dummy_window(i * 5) for i in range(3)]
    ground_truth = [True, False, True]

    # Specialist A flags window 0
    spec_a = MagicMock()
    spec_a.analyze.side_effect = [
        SpecialistOpinion(
            window_id=windows[0].window_id,
            subsystem=Subsystem.POWER,
            anomaly_score=0.8,
            severity=Severity.WARNING,
            threshold_used=0.5,
            model_run_id="run-power",
        ),
        SpecialistOpinion(
            window_id=windows[1].window_id,
            subsystem=Subsystem.POWER,
            anomaly_score=0.1,
            severity=Severity.NOMINAL,
            threshold_used=0.5,
            model_run_id="run-power",
        ),
        SpecialistOpinion(
            window_id=windows[2].window_id,
            subsystem=Subsystem.POWER,
            anomaly_score=0.1,
            severity=Severity.NOMINAL,
            threshold_used=0.5,
            model_run_id="run-power",
        ),
    ]

    # Specialist B flags window 2
    spec_b = MagicMock()
    spec_b.analyze.side_effect = [
        SpecialistOpinion(
            window_id=windows[0].window_id,
            subsystem=Subsystem.THERMAL,
            anomaly_score=0.1,
            severity=Severity.NOMINAL,
            threshold_used=0.5,
            model_run_id="run-thermal",
        ),
        SpecialistOpinion(
            window_id=windows[1].window_id,
            subsystem=Subsystem.THERMAL,
            anomaly_score=0.1,
            severity=Severity.NOMINAL,
            threshold_used=0.5,
            model_run_id="run-thermal",
        ),
        SpecialistOpinion(
            window_id=windows[2].window_id,
            subsystem=Subsystem.THERMAL,
            anomaly_score=0.9,
            severity=Severity.CRITICAL,
            threshold_used=0.5,
            model_run_id="run-thermal",
        ),
    ]

    def make_nom_spec(sub: Subsystem) -> MagicMock:
        m = MagicMock()
        m.analyze.return_value = SpecialistOpinion(
            window_id=windows[0].window_id,
            subsystem=sub,
            anomaly_score=0.1,
            severity=Severity.NOMINAL,
            threshold_used=0.5,
            model_run_id=f"run-{sub.value}",
        )
        return m

    results = run_ablation(
        windows=windows,
        arms=("D",),
        ground_truth=ground_truth,
        models={
            "D": {
                "power": spec_a,
                "thermal": spec_b,
                "attitude": make_nom_spec(Subsystem.ATTITUDE),
                "communications": make_nom_spec(Subsystem.COMMUNICATIONS),
            }
        },
    )

    res_d = results["D"]
    assert res_d["status"] == "EXECUTED"
    assert res_d["subsystem_predictions"]["power"] == [True, False, False]
    assert res_d["subsystem_predictions"]["thermal"] == [False, False, True]
    assert res_d["predictions"] == [True, False, True]
    assert res_d["precision"] == 1.0
    assert res_d["recall"] == 1.0
    assert res_d["f1"] == 1.0
    assert res_d["false_positive_rate"] == 0.0


def test_run_ablation_arm_e_default_orchestrator_blocked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify Arm E dynamically invokes default orchestrator and catches NotImplementedError."""

    def mock_not_implemented(*args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError("run_pipeline: pending")

    monkeypatch.setattr("services.orchestrator.graph.run_pipeline", mock_not_implemented)
    windows = [_make_dummy_window(0)]
    results = run_ablation(windows=windows, arms=("E",))

    assert "E" in results
    arm_e = results["E"]
    assert arm_e["status"] == "BLOCKED_PENDING_TIER_3"
    assert "run_pipeline" in arm_e["blocker"]
    assert any("services.orchestrator.graph" in b for b in arm_e["blockers"])
    assert "predictions" not in arm_e


def test_run_ablation_arm_e_default_orchestrator_operational_mock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify Arm E default pipeline execution when orchestrator run_pipeline is operational."""
    import services.orchestrator.graph as orch_graph

    windows = [_make_dummy_window(0), _make_dummy_window(5)]
    ground_truth = [True, False]

    def mock_run_pipeline(window_dict: dict[str, Any]) -> dict[str, Any]:
        # Return operational pipeline result
        is_anom = window_dict["start_time"].minute == 0
        return {
            "window_id": window_dict["window_id"],
            "decision": MagicMock(is_anomalous=is_anom),
            "severity": Severity.CRITICAL if is_anom else Severity.NOMINAL,
        }

    monkeypatch.setattr(orch_graph, "run_pipeline", mock_run_pipeline)

    results = run_ablation(
        windows=windows,
        arms=("E",),
        ground_truth=ground_truth,
    )

    assert "E" in results
    arm_e = results["E"]
    assert arm_e["status"] == "EXECUTED_DEFAULT_PIPELINE"
    assert arm_e["predictions"] == [True, False]
    assert arm_e["precision"] == 1.0
    assert arm_e["recall"] == 1.0
    assert arm_e["f1"] == 1.0


def test_run_ablation_arm_e_does_not_mask_unrelated_exceptions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify Arm E does not swallow unrelated non-NotImplementedError exceptions."""
    import services.orchestrator.graph as orch_graph

    windows = [_make_dummy_window(0)]

    def broken_run_pipeline(window_dict: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("Unexpected pipeline execution hardware failure")

    monkeypatch.setattr(orch_graph, "run_pipeline", broken_run_pipeline)

    with pytest.raises(RuntimeError, match="Unexpected pipeline execution hardware failure"):
        run_ablation(windows=windows, arms=("E",))


def test_model_interface_validation() -> None:
    """Verify model interface validation for invalid model types in Arm D."""
    windows = [_make_dummy_window(0)]

    # Non-executable string model
    res_str = run_ablation(windows=windows, arms=("D",), models={"D": "invalid_string_model"})
    res_d_str = res_str["D"]
    assert res_d_str["status"] == "UNAVAILABLE"

    # Non-executable list of numbers
    res_list = run_ablation(windows=windows, arms=("D",), models={"D": [1, 2, 3]})
    res_d_list = res_list["D"]
    assert res_d_list["status"] == "UNAVAILABLE"


def test_run_ablation_arm_d_missing_specialist_returns_unavailable() -> None:
    """Verify Arm D returns UNAVAILABLE when any one of the four required specialists is missing."""
    windows = [_make_dummy_window(0)]
    mock_spec = MagicMock()
    mock_spec.analyze.return_value = SpecialistOpinion(
        window_id=windows[0].window_id,
        subsystem=Subsystem.POWER,
        anomaly_score=0.1,
        severity=Severity.NOMINAL,
        threshold_used=0.5,
        model_run_id="run-power",
    )
    # Only 3 specialists provided: power, thermal, attitude. communications is missing.
    partial_models = {
        "power": mock_spec,
        "thermal": mock_spec,
        "attitude": mock_spec,
    }
    results = run_ablation(windows=windows, arms=("D",), models={"D": partial_models})
    assert "D" in results
    res_d = results["D"]
    assert res_d["status"] == "UNAVAILABLE"
    assert "communications" in res_d["error"]
    assert "predictions" not in res_d
    assert "anomaly_count" not in res_d


def test_run_ablation_arm_d_subsystem_normalization_and_all_four_required() -> None:
    """Verify Arm D normalizes enum, prefix, and string subsystem keys and executes with all 4."""
    windows = [_make_dummy_window(0)]

    def make_spec(sub: Subsystem) -> MagicMock:
        m = MagicMock()
        m.analyze.return_value = SpecialistOpinion(
            window_id=windows[0].window_id,
            subsystem=sub,
            anomaly_score=0.1,
            severity=Severity.NOMINAL,
            threshold_used=0.5,
            model_run_id=f"run-{sub.value}",
        )
        return m

    # Mixed key formats: enum, uppercase, prefix, and standard string
    models_d = {
        Subsystem.POWER: make_spec(Subsystem.POWER),
        "THERMAL": make_spec(Subsystem.THERMAL),
        "subsystem.attitude": make_spec(Subsystem.ATTITUDE),
        "communications": make_spec(Subsystem.COMMUNICATIONS),
    }
    results = run_ablation(windows=windows, arms=("D",), models={"D": models_d})
    assert results["D"]["status"] == "EXECUTED"
    assert set(results["D"]["subsystems_evaluated"]) == {
        "power",
        "thermal",
        "attitude",
        "communications",
    }


def test_run_ablation_arm_e_parses_actual_fusion_decision() -> None:
    """Verify Arm E correctly parses an actual FusionDecision contract instance."""
    windows = [_make_dummy_window(0), _make_dummy_window(5)]
    ground_truth = [True, False]

    def mock_pipeline(w: TelemetryWindow) -> FusionDecision:
        is_anom = w.start_time.minute == 0
        return FusionDecision(
            window_id=w.window_id,
            opinions=[],
            severity=Severity.CRITICAL if is_anom else Severity.NOMINAL,
            fusion_rule_applied="corroborated_alert" if is_anom else "nominal_baseline",
        )

    # Directly returned FusionDecision
    results = run_ablation(
        windows=windows,
        arms=("E",),
        ground_truth=ground_truth,
        pipeline_fn=mock_pipeline,
    )
    assert "E" in results
    arm_e = results["E"]
    assert arm_e["status"] == "EXECUTED_WITH_INJECTED_PIPELINE"
    assert arm_e["predictions"] == [True, False]
    assert arm_e["precision"] == 1.0
    assert arm_e["recall"] == 1.0
    assert arm_e["f1"] == 1.0

    # Wrapped in dictionary per orchestrator return contract
    def wrapped_pipeline(w: TelemetryWindow) -> dict[str, Any]:
        return {"fusion_decision": mock_pipeline(w)}

    results_wrapped = run_ablation(windows=windows, arms=("E",), pipeline_fn=wrapped_pipeline)
    assert results_wrapped["E"]["predictions"] == [True, False]


def test_run_ablation_arm_e_rejects_invalid_pipeline_result() -> None:
    """Verify Arm E raises ValueError on invalid or unrecognized pipeline outputs."""
    windows = [_make_dummy_window(0)]

    # Unknown string output
    with pytest.raises(ValueError, match="invalid or unrecognized pipeline output"):
        run_ablation(windows=windows, arms=("E",), pipeline_fn=lambda w: "unknown_string")

    # Empty dictionary output
    with pytest.raises(ValueError, match="invalid or unrecognized pipeline output"):
        run_ablation(windows=windows, arms=("E",), pipeline_fn=lambda w: {})

    # Unrecognized primitive without decision or anomaly flag
    with pytest.raises(ValueError, match="invalid or unrecognized pipeline output"):
        run_ablation(windows=windows, arms=("E",), pipeline_fn=lambda w: 42)


def test_run_ablation_arm_e_does_not_retry_on_internal_type_error() -> None:
    """Verify Arm E does not catch or retry when the pipeline function raises an internal TypeError."""
    windows = [_make_dummy_window(0)]
    call_count = 0

    def pipeline_with_internal_type_error(w: TelemetryWindow) -> Any:
        nonlocal call_count
        call_count += 1
        raise TypeError("Internal TypeError inside pipeline parser")

    with pytest.raises(TypeError, match="Internal TypeError inside pipeline parser"):
        run_ablation(windows=windows, arms=("E",), pipeline_fn=pipeline_with_internal_type_error)

    # Must have been called exactly once without retry
    assert call_count == 1
