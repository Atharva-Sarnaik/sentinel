"""
tests.unit.test_specialists
===========================
Unit tests for shared PyTorch LSTM-AE template (T1.3) and Dynamic Thresholding (T1.4).

Owner:   Atharva Sarnaik (@Atharva-Sarnaik) / Sujal Hede (@Sujalhede)
Tier:    1 (tasks T1.3 & T1.4)
Status:  complete — validates model training, reconstruction, threshold calibration, and save/load.
"""

from __future__ import annotations

import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from libs.contracts import Severity, Subsystem, TelemetryWindow
from services.specialists.lstm_ae_template import LSTMAETemplate
from services.specialists.specialist import SpecialistDetector
from services.specialists.thresholding import DynamicThresholder
from services.specialists.train import train_all_from_configs, train_specialist


@pytest.fixture
def specialist_config() -> dict:
    return {
        "subsystem": "power",
        "channels": ["P-1", "P-2"],
        "model": {
            "lstm_hidden_size": 16,
            "lstm_num_layers": 1,
            "latent_dim": 8,
            "epochs": 3,
            "batch_size": 4,
            "learning_rate": 0.01,
        },
    }


@pytest.fixture
def training_windows() -> list[TelemetryWindow]:
    t0 = datetime(2024, 1, 1, 0, 0, tzinfo=UTC)
    windows = []
    for i in range(12):
        start = t0 + timedelta(minutes=i * 5)
        end = start + timedelta(minutes=4)
        windows.append(
            TelemetryWindow(
                subsystem=Subsystem.POWER,
                start_time=start,
                end_time=end,
                channels={
                    "P-1": [1.0 + 0.05 * (j % 5) for j in range(30)],
                    "P-2": [0.5 + 0.02 * (j % 3) for j in range(30)],
                },
                source_dataset="SMAP",
            )
        )
    return windows


# ---------------------------------------------------------------------------
# DynamicThresholder Tests (T1.4)
# ---------------------------------------------------------------------------


def test_dynamic_thresholder_calibration() -> None:
    errors = [0.01, 0.012, 0.011, 0.009, 0.013, 0.01, 0.014, 0.012]
    thresholder = DynamicThresholder(default_percentile=95.0)
    thresholder.fit(errors)

    assert thresholder.is_fitted is True
    assert thresholder.threshold_value > 0.01

    # In-distribution error should be nominal
    assert thresholder.predict(0.01) is False
    assert thresholder.severity_for(0.01) == Severity.NOMINAL
    assert thresholder.score(0.01) < 0.5

    # High anomaly error should trigger alert
    extreme_err = thresholder.threshold_value * 2.0
    assert thresholder.predict(extreme_err) is True
    assert thresholder.severity_for(extreme_err) == Severity.CRITICAL
    assert thresholder.score(extreme_err) > 0.5


# ---------------------------------------------------------------------------
# LSTMAETemplate Tests (T1.3)
# ---------------------------------------------------------------------------


def test_lstm_ae_train_and_reconstruct(
    specialist_config: dict,
    training_windows: list[TelemetryWindow],
) -> None:
    specialist = LSTMAETemplate(specialist_config)
    assert specialist.is_trained is False

    loss_history = specialist.train(training_windows, epochs=2)
    assert specialist.is_trained is True
    assert len(loss_history) == 2
    assert all(loss > 0 for loss in loss_history)

    # Reconstruct a window
    recon = specialist.reconstruct(training_windows[0])
    assert recon.shape == (30, 2)

    # Reconstruction error
    err = specialist.reconstruction_error(training_windows[0])
    assert isinstance(err, float)
    assert err >= 0.0

    # Channel errors
    ch_errs = specialist.channel_reconstruction_errors(training_windows[0])
    assert "P-1" in ch_errs
    assert "P-2" in ch_errs


def test_lstm_ae_save_and_load(
    specialist_config: dict,
    training_windows: list[TelemetryWindow],
) -> None:
    specialist = LSTMAETemplate(specialist_config)
    specialist.train(training_windows, epochs=1)

    with tempfile.NamedTemporaryFile("wb", suffix=".pt", delete=False) as tf:
        model_path = Path(tf.name)

    try:
        specialist.save(model_path)
        loaded = LSTMAETemplate.load(model_path, specialist_config)
        assert loaded.is_trained is True
        err = loaded.reconstruction_error(training_windows[0])
        assert isinstance(err, float)
    finally:
        model_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# SpecialistDetector and Training Tests (T1.5)
# ---------------------------------------------------------------------------


def test_specialist_detector_inference_and_persistence(
    specialist_config: dict,
    training_windows: list[TelemetryWindow],
) -> None:
    detector, metrics = train_specialist(
        config=specialist_config,
        train_windows=training_windows,
        val_windows=training_windows[:3],
        epochs=2,
    )
    assert detector.subsystem == Subsystem.POWER
    assert "threshold" in metrics
    assert metrics["n_train"] == len(training_windows)
    assert metrics["n_eval"] == 3

    # Test analyze
    opinion = detector.analyze(training_windows[0])
    assert opinion.subsystem == Subsystem.POWER
    assert 0.0 <= opinion.anomaly_score <= 1.0
    assert opinion.threshold_used == metrics["threshold"]

    # Test save and load
    with tempfile.NamedTemporaryFile("wb", suffix=".pt", delete=False) as tf:
        model_path = Path(tf.name)

    try:
        detector.save(model_path)
        loaded = SpecialistDetector.load(model_path)
        assert loaded.subsystem == Subsystem.POWER
        loaded_op = loaded.analyze(training_windows[0])
        assert loaded_op.anomaly_score == opinion.anomaly_score
    finally:
        model_path.unlink(missing_ok=True)


def test_train_all_from_configs(
    training_windows: list[TelemetryWindow],
    tmp_path: Path,
) -> None:
    # Point to the actual specialist configs
    config_dir = Path("services/specialists/configs")
    output_dir = tmp_path / "models"

    results = train_all_from_configs(
        config_dir=config_dir,
        train_windows=training_windows,
        val_windows=training_windows[:2],
        output_dir=output_dir,
        epochs=1,
    )

    assert len(results) == 4
    for sub in ["power", "thermal", "attitude", "communications"]:
        assert sub in results
        assert results[sub]["n_train"] == len(training_windows)
        assert Path(results[sub]["saved_path"]).is_file()
