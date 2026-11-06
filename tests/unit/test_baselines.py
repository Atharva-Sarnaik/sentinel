"""
tests.unit.test_baselines
=========================
Unit tests for Arm A (Static Threshold) and Arm B (Isolation Forest) baselines.

Owner:   Sujal Hede (@Sujalhede) / Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    1 (tasks T1.1 & T1.2)
Status:  complete — tests calibration, training, prediction, and edge cases.
"""

from __future__ import annotations

import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from libs.contracts import Severity, Subsystem, TelemetryWindow
from services.baselines.combined_lstm_ae import CombinedLSTMAEDetector, run_combined_lstm_ae
from services.baselines.isolation_forest import IsolationForestBaseline, run_isolation_forest
from services.baselines.static_threshold import calibrate_static_thresholds, run_static_threshold


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
# Arm A: Static Threshold Tests
# ---------------------------------------------------------------------------


def test_static_threshold_normal(normal_training_windows: list[TelemetryWindow]) -> None:
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
    thresholds = calibrate_static_thresholds(normal_training_windows, percentile=99.0)
    opinion = run_static_threshold(anomalous_window, thresholds)

    assert opinion.severity in (Severity.WARNING, Severity.CRITICAL)
    assert opinion.anomaly_score > 0.5
    assert "P-1" in opinion.responsible_channels


# ---------------------------------------------------------------------------
# Arm B: Isolation Forest Tests
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
# Arm C: Combined LSTM-AE Tests
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
