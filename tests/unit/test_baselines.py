"""
tests.unit.test_baselines
=========================
Unit tests for Arm A (Static Threshold) and Arm B (Isolation Forest) baselines.

Owner:   Sujal Hede (@Sujalhede) / Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    1 (tasks T1.1 & T1.2)
Status:  complete — tests calibration, training, prediction, two-sided bounds,
         numerical validation, persistence, and evaluation metrics.
"""

from __future__ import annotations

import json
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from libs.contracts import Severity, Subsystem, TelemetryWindow
from services.baselines.combined_lstm_ae import CombinedLSTMAEDetector, run_combined_lstm_ae
from services.baselines.isolation_forest import IsolationForestBaseline, run_isolation_forest
from services.baselines.static_threshold import (
    ChannelThreshold,
    StaticThresholdBaseline,
    calibrate_static_thresholds,
    evaluate_static_threshold,
    run_static_threshold,
)


@pytest.fixture
def normal_training_windows() -> list[TelemetryWindow]:
    """25 normal healthy telemetry windows with slight natural variance."""
    t0 = datetime(2024, 1, 1, 0, 0, tzinfo=UTC)
    windows = []
    for i in range(25):
        start = t0 + timedelta(minutes=i * 5)
        end = start + timedelta(minutes=4)
        noise = 0.05 * (i % 7)
        windows.append(
            TelemetryWindow(
                subsystem=Subsystem.POWER,
                start_time=start,
                end_time=end,
                channels={
                    "P-1": [28.0 + noise + 0.1 * ((j % 5) - 2) for j in range(50)],
                    "P-2": [5.0 + noise * 0.2 + 0.05 * ((j % 3) - 1) for j in range(50)],
                },
                source_dataset="SMAP",
            )
        )
    return windows


@pytest.fixture
def anomalous_window() -> TelemetryWindow:
    """Telemetry window with an anomalous voltage spike on P-1."""
    t0 = datetime(2024, 1, 2, 0, 0, tzinfo=UTC)
    return TelemetryWindow(
        subsystem=Subsystem.POWER,
        start_time=t0,
        end_time=t0 + timedelta(minutes=4),
        channels={
            "P-1": [55.0] * 50,  # Extreme spike (nominal 28V)
            "P-2": [5.0] * 50,
        },
        source_dataset="SMAP",
    )


# ---------------------------------------------------------------------------
# Arm A: Static Threshold Tests (Preserved + Enhanced)
# ---------------------------------------------------------------------------


def test_static_threshold_normal(normal_training_windows: list[TelemetryWindow]) -> None:
    """Preserved baseline test: normal window yields NOMINAL severity."""
    thresholds = calibrate_static_thresholds(normal_training_windows, percentile=99.0)
    assert "P-1" in thresholds
    assert thresholds["P-1"] >= 28.2

    # Normal window should yield NOMINAL
    opinion = run_static_threshold(normal_training_windows[0], thresholds)
    assert opinion.severity == Severity.NOMINAL
    assert opinion.anomaly_score == 0.0
    assert len(opinion.responsible_channels) == 0


def test_static_threshold_anomaly(
    normal_training_windows: list[TelemetryWindow],
    anomalous_window: TelemetryWindow,
) -> None:
    """Preserved baseline test: high spike yields anomaly on P-1."""
    thresholds = calibrate_static_thresholds(normal_training_windows, percentile=99.0)
    opinion = run_static_threshold(anomalous_window, thresholds)

    assert opinion.severity in (Severity.WARNING, Severity.CRITICAL)
    assert opinion.anomaly_score > 0.5
    assert "P-1" in opinion.responsible_channels


def test_static_threshold_inside_bounds(normal_training_windows: list[TelemetryWindow]) -> None:
    """Scenario 1: Normal telemetry inside both lower and upper bounds."""
    thresholds = calibrate_static_thresholds(
        normal_training_windows, lower_percentile=0.5, upper_percentile=99.5
    )
    assert isinstance(thresholds["P-1"], ChannelThreshold)
    assert thresholds["P-1"].lower <= 27.8
    assert thresholds["P-1"].upper >= 28.4

    for w in normal_training_windows[:5]:
        opinion = run_static_threshold(w, thresholds)
        assert opinion.severity == Severity.NOMINAL
        assert opinion.anomaly_score == 0.0
        assert not opinion.is_anomalous
        assert len(opinion.responsible_channels) == 0


def test_static_threshold_upper_bound_violation(
    normal_training_windows: list[TelemetryWindow],
) -> None:
    """Scenario 2: Single upper-bound violation triggers anomaly."""
    thresholds = calibrate_static_thresholds(normal_training_windows)
    t0 = datetime(2024, 1, 3, 0, 0, tzinfo=UTC)
    spike_window = TelemetryWindow(
        subsystem=Subsystem.POWER,
        start_time=t0,
        end_time=t0 + timedelta(minutes=4),
        channels={
            "P-1": [45.0] * 50,  # exceeds upper (~28.5)
            "P-2": [5.0] * 50,
        },
        source_dataset="SMAP",
    )
    opinion = run_static_threshold(spike_window, thresholds)
    assert opinion.is_anomalous
    assert "P-1" in opinion.responsible_channels
    assert "P-2" not in opinion.responsible_channels
    assert opinion.severity in (Severity.WARNING, Severity.CRITICAL)


def test_static_threshold_lower_bound_violation(
    normal_training_windows: list[TelemetryWindow],
) -> None:
    """Scenario 3: Single lower-bound violation triggers anomaly."""
    thresholds = calibrate_static_thresholds(normal_training_windows)
    t0 = datetime(2024, 1, 3, 0, 0, tzinfo=UTC)
    drop_window = TelemetryWindow(
        subsystem=Subsystem.POWER,
        start_time=t0,
        end_time=t0 + timedelta(minutes=4),
        channels={
            "P-1": [12.0] * 50,  # below lower (~27.8)
            "P-2": [5.0] * 50,
        },
        source_dataset="SMAP",
    )
    opinion = run_static_threshold(drop_window, thresholds)
    assert opinion.is_anomalous
    assert "P-1" in opinion.responsible_channels
    assert "P-2" not in opinion.responsible_channels
    assert opinion.severity in (Severity.WARNING, Severity.CRITICAL)


def test_static_threshold_both_upper_and_lower_violations(
    normal_training_windows: list[TelemetryWindow],
) -> None:
    """Scenario 4: Channels violating upper and lower bounds simultaneously."""
    thresholds = calibrate_static_thresholds(normal_training_windows)
    t0 = datetime(2024, 1, 3, 0, 0, tzinfo=UTC)
    dual_window = TelemetryWindow(
        subsystem=Subsystem.POWER,
        start_time=t0,
        end_time=t0 + timedelta(minutes=4),
        channels={
            "P-1": [50.0] * 50,  # upper violation
            "P-2": [1.0] * 50,  # lower violation (nominal ~5.0)
        },
        source_dataset="SMAP",
    )
    opinion = run_static_threshold(dual_window, thresholds)
    assert opinion.is_anomalous
    assert "P-1" in opinion.responsible_channels
    assert "P-2" in opinion.responsible_channels
    assert opinion.severity == Severity.CRITICAL  # >=2 channels violated


def test_static_threshold_independent_channels() -> None:
    """Scenario 5: Independent per-channel threshold behavior."""
    custom_thresholds = {
        "P-1": ChannelThreshold(lower=20.0, upper=30.0),
        "P-2": ChannelThreshold(lower=4.0, upper=6.0),
    }
    t0 = datetime(2024, 1, 3, 0, 0, tzinfo=UTC)

    # Window with P-1 anomalous (35.0) but P-2 healthy (5.0)
    w1 = TelemetryWindow(
        subsystem=Subsystem.POWER,
        start_time=t0,
        end_time=t0 + timedelta(minutes=4),
        channels={"P-1": [35.0] * 50, "P-2": [5.0] * 50},
        source_dataset="SMAP",
    )
    op1 = run_static_threshold(w1, custom_thresholds)
    assert op1.responsible_channels == ["P-1"]

    # Window with P-1 healthy (25.0) but P-2 anomalous (2.0)
    w2 = TelemetryWindow(
        subsystem=Subsystem.POWER,
        start_time=t0,
        end_time=t0 + timedelta(minutes=4),
        channels={"P-1": [25.0] * 50, "P-2": [2.0] * 50},
        source_dataset="SMAP",
    )
    op2 = run_static_threshold(w2, custom_thresholds)
    assert op2.responsible_channels == ["P-2"]


def test_static_threshold_nan_rejection_calibration(
    normal_training_windows: list[TelemetryWindow],
) -> None:
    """Scenario 6: NaN value during calibration raises informative ValueError."""
    bad_window = TelemetryWindow(
        subsystem=Subsystem.POWER,
        start_time=datetime(2024, 1, 1, tzinfo=UTC),
        end_time=datetime(2024, 1, 1, 0, 4, tzinfo=UTC),
        channels={"P-1": [28.0, float("nan")] + [28.0] * 48},
        source_dataset="SMAP",
    )
    windows = list(normal_training_windows) + [bad_window]
    with pytest.raises(ValueError, match="NaN and Inf are rejected"):
        calibrate_static_thresholds(windows)


def test_static_threshold_inf_rejection_calibration(
    normal_training_windows: list[TelemetryWindow],
) -> None:
    """Scenario 7: Positive/negative infinity during calibration raises ValueError."""
    bad_pos_inf = TelemetryWindow(
        subsystem=Subsystem.POWER,
        start_time=datetime(2024, 1, 1, tzinfo=UTC),
        end_time=datetime(2024, 1, 1, 0, 4, tzinfo=UTC),
        channels={"P-1": [float("inf")] * 50},
        source_dataset="SMAP",
    )
    bad_neg_inf = TelemetryWindow(
        subsystem=Subsystem.POWER,
        start_time=datetime(2024, 1, 1, tzinfo=UTC),
        end_time=datetime(2024, 1, 1, 0, 4, tzinfo=UTC),
        channels={"P-1": [float("-inf")] * 50},
        source_dataset="SMAP",
    )
    with pytest.raises(ValueError, match="NaN and Inf are rejected"):
        calibrate_static_thresholds([bad_pos_inf])
    with pytest.raises(ValueError, match="NaN and Inf are rejected"):
        calibrate_static_thresholds([bad_neg_inf])


def test_static_threshold_nan_rejection_inference(
    normal_training_windows: list[TelemetryWindow],
) -> None:
    """Scenario 8: NaN value during inference raises ValueError."""
    thresholds = calibrate_static_thresholds(normal_training_windows)
    bad_window = TelemetryWindow(
        subsystem=Subsystem.POWER,
        start_time=datetime(2024, 1, 1, tzinfo=UTC),
        end_time=datetime(2024, 1, 1, 0, 4, tzinfo=UTC),
        channels={"P-1": [28.0, float("nan")] + [28.0] * 48},
        source_dataset="SMAP",
    )
    with pytest.raises(ValueError, match="NaN and Inf are rejected"):
        run_static_threshold(bad_window, thresholds)


def test_static_threshold_inf_rejection_inference(
    normal_training_windows: list[TelemetryWindow],
) -> None:
    """Scenario 9: Positive and negative Inf during inference raise ValueError."""
    thresholds = calibrate_static_thresholds(normal_training_windows)
    bad_pos = TelemetryWindow(
        subsystem=Subsystem.POWER,
        start_time=datetime(2024, 1, 1, tzinfo=UTC),
        end_time=datetime(2024, 1, 1, 0, 4, tzinfo=UTC),
        channels={"P-1": [float("inf")] * 50},
        source_dataset="SMAP",
    )
    bad_neg = TelemetryWindow(
        subsystem=Subsystem.POWER,
        start_time=datetime(2024, 1, 1, tzinfo=UTC),
        end_time=datetime(2024, 1, 1, 0, 4, tzinfo=UTC),
        channels={"P-1": [float("-inf")] * 50},
        source_dataset="SMAP",
    )
    with pytest.raises(ValueError, match="NaN and Inf are rejected"):
        run_static_threshold(bad_pos, thresholds)
    with pytest.raises(ValueError, match="NaN and Inf are rejected"):
        run_static_threshold(bad_neg, thresholds)


def test_static_threshold_empty_sequence_handling() -> None:
    """Scenario 10: Empty channel sequence raises informative ValueError."""
    empty_series_window = TelemetryWindow(
        subsystem=Subsystem.POWER,
        start_time=datetime(2024, 1, 1, tzinfo=UTC),
        end_time=datetime(2024, 1, 1, 0, 4, tzinfo=UTC),
        channels={"P-1": []},
        source_dataset="SMAP",
    )
    with pytest.raises(ValueError, match="empty sequence"):
        calibrate_static_thresholds([empty_series_window])

    dummy_thresholds = {"P-1": ChannelThreshold(lower=20.0, upper=30.0)}
    with pytest.raises(ValueError, match="empty sequence"):
        run_static_threshold(empty_series_window, dummy_thresholds)


def test_static_threshold_invalid_bounds_validation() -> None:
    """Scenario 11: Invalid threshold bounds (lower > upper or non-finite) raise ValueError."""
    with pytest.raises(ValueError, match="cannot exceed upper bound"):
        ChannelThreshold(lower=35.0, upper=25.0)

    with pytest.raises(ValueError, match="finite number"):
        ChannelThreshold(lower=float("nan"), upper=25.0)

    with pytest.raises(ValueError, match="finite number"):
        ChannelThreshold(lower=10.0, upper=float("inf"))


def test_static_threshold_save_and_load_roundtrip(
    normal_training_windows: list[TelemetryWindow],
    anomalous_window: TelemetryWindow,
) -> None:
    """Scenario 12: Baseline JSON persistence round-trip preserves state and predictions."""
    baseline = StaticThresholdBaseline().fit(normal_training_windows)

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
        model_path = Path(tf.name)

    try:
        baseline.save(model_path)
        loaded = StaticThresholdBaseline.load(model_path)

        assert loaded.thresholds.keys() == baseline.thresholds.keys()
        for ch in baseline.thresholds:
            assert loaded.thresholds[ch].lower == baseline.thresholds[ch].lower
            assert loaded.thresholds[ch].upper == baseline.thresholds[ch].upper

        # Verify predictions match exactly
        op_orig = baseline.predict(anomalous_window)
        op_loaded = loaded.predict(anomalous_window)
        assert op_loaded.anomaly_score == op_orig.anomaly_score
        assert op_loaded.severity == op_orig.severity
        assert op_loaded.responsible_channels == op_orig.responsible_channels
    finally:
        model_path.unlink(missing_ok=True)


def test_static_threshold_malformed_json_load() -> None:
    """Scenario 13: Corrupted or malformed JSON raises ValueError on load."""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
        tf.write("{ this is invalid json !!! ")
        model_path = Path(tf.name)

    try:
        with pytest.raises(ValueError, match="Malformed JSON"):
            StaticThresholdBaseline.load(model_path)
    finally:
        model_path.unlink(missing_ok=True)


def test_static_threshold_unsupported_schema_version() -> None:
    """Scenario 14: Unsupported schema version raises ValueError on load."""
    invalid_schema_payload = {
        "schema_version": "99.0",
        "thresholds": {"P-1": {"lower": 20.0, "upper": 30.0}},
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
        json.dump(invalid_schema_payload, tf)
        model_path = Path(tf.name)

    try:
        with pytest.raises(ValueError, match="Unsupported schema version"):
            StaticThresholdBaseline.load(model_path)
    finally:
        model_path.unlink(missing_ok=True)


def test_static_threshold_evaluation_metrics() -> None:
    """Scenario 15: Evaluation helper accurately calculates TP, FP, TN, FN, precision, recall, F1, FPR."""
    thresholds = {"P-1": ChannelThreshold(lower=20.0, upper=30.0)}
    t0 = datetime(2024, 1, 1, tzinfo=UTC)

    def make_window(val: float, idx: int) -> TelemetryWindow:
        return TelemetryWindow(
            subsystem=Subsystem.POWER,
            start_time=t0 + timedelta(minutes=idx * 5),
            end_time=t0 + timedelta(minutes=idx * 5 + 4),
            channels={"P-1": [val] * 10},
            source_dataset="SMAP",
        )

    # 4 windows:
    # w0: val=35 (anom), label=True  -> TP
    # w1: val=35 (anom), label=False -> FP
    # w2: val=25 (norm), label=False -> TN
    # w3: val=25 (norm), label=True  -> FN
    test_windows = [
        make_window(35.0, 0),
        make_window(35.0, 1),
        make_window(25.0, 2),
        make_window(25.0, 3),
    ]
    labels = [True, False, False, True]

    metrics = evaluate_static_threshold(test_windows, thresholds, labels)

    assert metrics["true_positives"] == 1
    assert metrics["false_positives"] == 1
    assert metrics["true_negatives"] == 1
    assert metrics["false_negatives"] == 1

    # Precision: TP / (TP + FP) = 1 / 2 = 0.5
    assert metrics["precision"] == 0.5
    # Recall: TP / (TP + FN) = 1 / 2 = 0.5
    assert metrics["recall"] == 0.5
    # F1: 2 * (0.5 * 0.5) / (0.5 + 0.5) = 0.5
    assert metrics["f1"] == 0.5
    # FPR: FP / (FP + TN) = 1 / 2 = 0.5
    assert metrics["false_positive_rate"] == 0.5


def test_static_threshold_evaluation_label_mismatch() -> None:
    """Scenario 16: Ground-truth label count mismatch raises ValueError."""
    thresholds = {"P-1": ChannelThreshold(lower=20.0, upper=30.0)}
    t0 = datetime(2024, 1, 1, tzinfo=UTC)
    w = TelemetryWindow(
        subsystem=Subsystem.POWER,
        start_time=t0,
        end_time=t0 + timedelta(minutes=4),
        channels={"P-1": [25.0] * 10},
        source_dataset="SMAP",
    )
    with pytest.raises(ValueError, match="Length mismatch"):
        evaluate_static_threshold([w], thresholds, [True, False])


def test_static_threshold_evaluation_zero_division() -> None:
    """Scenario 17: Zero-division handling produces 0.0 without errors."""
    thresholds = {"P-1": ChannelThreshold(lower=20.0, upper=30.0)}
    t0 = datetime(2024, 1, 1, tzinfo=UTC)
    w_norm = TelemetryWindow(
        subsystem=Subsystem.POWER,
        start_time=t0,
        end_time=t0 + timedelta(minutes=4),
        channels={"P-1": [25.0] * 10},
        source_dataset="SMAP",
    )

    # All normal observations and normal ground truth (TP=0, FP=0, TN=2, FN=0)
    metrics_all_normal = evaluate_static_threshold([w_norm, w_norm], thresholds, [False, False])
    assert metrics_all_normal["precision"] == 0.0
    assert metrics_all_normal["recall"] == 0.0
    assert metrics_all_normal["f1"] == 0.0
    assert metrics_all_normal["false_positive_rate"] == 0.0

    w_anom = TelemetryWindow(
        subsystem=Subsystem.POWER,
        start_time=t0,
        end_time=t0 + timedelta(minutes=4),
        channels={"P-1": [35.0] * 10},
        source_dataset="SMAP",
    )
    # All anomalous observations and anomalous ground truth (TP=2, FP=0, TN=0, FN=0)
    metrics_all_anom = evaluate_static_threshold([w_anom, w_anom], thresholds, [True, True])
    assert metrics_all_anom["precision"] == 1.0
    assert metrics_all_anom["recall"] == 1.0
    assert metrics_all_anom["f1"] == 1.0
    assert metrics_all_anom["false_positive_rate"] == 0.0


# ---------------------------------------------------------------------------
# Arm B: Isolation Forest Tests (Preserved)
# ---------------------------------------------------------------------------


def test_isolation_forest_train_and_predict(
    normal_training_windows: list[TelemetryWindow],
    anomalous_window: TelemetryWindow,
) -> None:
    detector = IsolationForestBaseline(n_estimators=50, random_state=42)
    detector.fit(normal_training_windows)
    assert detector.is_fitted is True

    # Test prediction on normal window
    norm_op = detector.predict(normal_training_windows[0])
    assert 0.0 <= norm_op.anomaly_score <= 1.0

    # Test prediction on anomalous window
    anom_op = detector.predict(anomalous_window)
    assert anom_op.anomaly_score > norm_op.anomaly_score


def test_isolation_forest_save_and_load(
    normal_training_windows: list[TelemetryWindow],
    anomalous_window: TelemetryWindow,
) -> None:
    detector = IsolationForestBaseline(n_estimators=30, random_state=42).fit(
        normal_training_windows
    )

    with tempfile.NamedTemporaryFile("wb", suffix=".pkl", delete=False) as tf:
        model_path = Path(tf.name)

    try:
        detector.save(model_path)
        loaded = IsolationForestBaseline.load(model_path)
        assert loaded.is_fitted is True

        op = run_isolation_forest(anomalous_window, loaded)
        assert 0.0 <= op.anomaly_score <= 1.0
    finally:
        model_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Arm C: Combined LSTM-AE Tests (Preserved)
# ---------------------------------------------------------------------------


def test_combined_lstm_ae_train_and_predict(
    normal_training_windows: list[TelemetryWindow],
    anomalous_window: TelemetryWindow,
) -> None:
    channels = ["P-1", "P-2"]
    detector = CombinedLSTMAEDetector(
        channels=channels,
        hidden_dim=16,
        num_layers=1,
        latent_dim=8,
    )
    metrics = detector.train(normal_training_windows, epochs=2, batch_size=8)
    assert detector.is_trained is True
    assert "loss_history" in metrics
    assert detector.threshold > 0.0

    # Predict normal
    norm_op = detector.predict(normal_training_windows[0])
    assert 0.0 <= norm_op.anomaly_score <= 1.0

    # Predict anomalous
    anom_op = detector.predict(anomalous_window)
    assert anom_op.anomaly_score > norm_op.anomaly_score
    assert len(anom_op.responsible_channels) >= 1


def test_combined_lstm_ae_save_and_load(
    normal_training_windows: list[TelemetryWindow],
    anomalous_window: TelemetryWindow,
) -> None:
    channels = ["P-1", "P-2"]
    detector = CombinedLSTMAEDetector(
        channels=channels,
        hidden_dim=16,
        num_layers=1,
        latent_dim=8,
    )
    detector.train(normal_training_windows, epochs=2, batch_size=8)

    with tempfile.NamedTemporaryFile("wb", suffix=".pt", delete=False) as tf:
        model_path = Path(tf.name)

    try:
        detector.save(model_path)
        opinion = run_combined_lstm_ae(anomalous_window, str(model_path))
        assert 0.0 <= opinion.anomaly_score <= 1.0
        assert opinion.threshold_used == detector.threshold
    finally:
        model_path.unlink(missing_ok=True)
