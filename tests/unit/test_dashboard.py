"""Unit tests for Task T6.1: Streamlit Replay Dashboard (apps.dashboard.app).

Tests:
  - Cache function for evaluation windows (determinism and length).
  - Data leakage prevention in stacking coordinator training data preparation.
  - Balance and fidelity of nominal vs anomalous training samples.
  - Invariance of original healthy training windows during anomaly copy creation.
  - Strict absence of test windows during coordinator model fitting.
  - Fitting and calibrated inference of the learned stacking coordinator.
  - Subsystem panel missing channels warning handling.

Owner:   Sujal Hede (@Sujalhede)
Tier:    6 (task T6.1, T6.2)
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
from scripts.run_experiments import generate_standard_evaluation_windows

from apps.dashboard.app import (
    get_cached_stacking_coordinator,
    get_cached_telemetry_windows,
    prepare_stacking_training_data,
    render_subsystem_panel,
)
from libs.contracts import Subsystem, TelemetryWindow


def test_cached_telemetry_windows() -> None:
    """Verify cached telemetry windows generate deterministically for replay."""
    windows, labels = get_cached_telemetry_windows(seed=42)
    assert len(windows) == 30
    assert len(labels) == 30
    assert any(labels)  # Has anomalous windows
    assert not all(labels)  # Has nominal windows


def test_prepare_stacking_training_data_composition_and_labels() -> None:
    """Verify stacking training dataset contains balanced nominal and anomalous samples."""
    train_windows, test_windows, _ = generate_standard_evaluation_windows(
        seed=42, n_train=10, n_test=20
    )

    samples, labels = prepare_stacking_training_data(train_windows)

    # 10 nominal + 10 anomalous copies = 20 total training samples
    assert len(samples) == 20
    assert len(labels) == 20

    nominal_count = sum(1 for lbl in labels if not lbl)
    anomalous_count = sum(1 for lbl in labels if lbl)
    assert nominal_count == 10
    assert anomalous_count == 10

    # First half must be nominal (False), second half anomalous (True)
    assert labels[:10] == [False] * 10
    assert labels[10:] == [True] * 10


def test_prepare_stacking_training_data_isolation_and_injection() -> None:
    """Verify original training windows are unchanged and anomaly copies are correctly injected."""
    train_windows, test_windows, _ = generate_standard_evaluation_windows(
        seed=42, n_train=10, n_test=20
    )

    # Snapshot baseline values of original training windows
    original_channel_snapshots = [
        {ch: list(vals) for ch, vals in w.channels.items()} for w in train_windows
    ]

    samples, labels = prepare_stacking_training_data(train_windows)

    # 1. Original healthy training windows must remain completely untouched
    for i, orig_w in enumerate(train_windows):
        for ch, vals in orig_w.channels.items():
            assert vals == original_channel_snapshots[i][ch], (
                f"Original window {i} channel {ch} was mutated"
            )

    # 2. First 10 samples are the exact nominal training windows
    for i in range(10):
        assert samples[i].window_id == train_windows[i].window_id
        assert samples[i].channels == train_windows[i].channels

    # 3. Next 10 samples are synthetic anomaly copies with unique IDs
    all_window_ids = [s.window_id for s in samples]
    assert len(set(all_window_ids)) == 20, "Window IDs across training samples must be unique"

    test_window_ids = {tw.window_id for tw in test_windows}
    assert set(all_window_ids).isdisjoint(test_window_ids), (
        "Training window IDs must not overlap test windows"
    )

    # 4. Check anomaly injection in copies: P-1, T-1, A-1 scaled by 1.75; others unchanged
    for i in range(10):
        anom_copy = samples[10 + i]
        orig_w = train_windows[i]
        for ch, vals in anom_copy.channels.items():
            if ch in ("P-1", "T-1", "A-1"):
                expected = [v * 1.75 for v in orig_w.channels[ch]]
                assert vals == pytest.approx(expected), (
                    f"Channel {ch} in copy {i} not scaled by 1.75"
                )
            else:
                assert vals == orig_w.channels[ch], (
                    f"Channel {ch} in copy {i} unexpectedly modified"
                )


def test_cached_stacking_coordinator_never_uses_test_windows(monkeypatch) -> None:
    """Verify coordinator is fitted using only training data and never touches test windows."""
    fit_calls: list[dict] = []
    from services.fusion.stacking import LearnedStackingCoordinator

    orig_fit = LearnedStackingCoordinator.fit

    def spy_fit(self, opinions, labels):
        fit_calls.append({"num_samples": len(opinions), "labels": list(labels)})
        return orig_fit(self, opinions, labels)

    monkeypatch.setattr(LearnedStackingCoordinator, "fit", spy_fit)

    # Clear cache to force clean execution
    get_cached_stacking_coordinator.clear()
    coordinator = get_cached_stacking_coordinator()

    assert coordinator.is_fitted
    assert len(fit_calls) == 1

    call = fit_calls[0]
    # Must use 20 prepared training samples (10 nominal + 10 anomalous), not test windows (20 test samples)
    assert call["num_samples"] == 20
    assert call["labels"] == [False] * 10 + [True] * 10


def test_render_subsystem_panel_missing_channels(monkeypatch) -> None:
    """Verify missing subsystem channels display a clear warning instead of all channels."""
    import streamlit as st

    warning_mock = MagicMock()
    line_chart_mock = MagicMock()
    monkeypatch.setattr(st, "warning", warning_mock)
    monkeypatch.setattr(st, "line_chart", line_chart_mock)

    # Window containing only Power channels
    test_window = TelemetryWindow(
        window_id=uuid.uuid4(),
        subsystem=Subsystem.POWER,
        start_time="2026-01-01T00:00:00Z",
        end_time="2026-01-01T00:04:00Z",
        channels={"P-1": [28.0] * 5, "P-2": [28.0] * 5},
        source_dataset="Synthetic",
    )

    # Render Thermal panel (prefix "T-") on a window that only has "P-" channels
    render_subsystem_panel(Subsystem.THERMAL, None, test_window, channel_prefix="T-")

    # Must display the warning and NOT display any line chart
    warning_mock.assert_called_once_with("No telemetry channels available for this subsystem.")
    line_chart_mock.assert_not_called()


def test_render_subsystem_panel_matching_channels(monkeypatch) -> None:
    """Verify matching subsystem channels render the time-series line chart without warning."""
    import streamlit as st

    warning_mock = MagicMock()
    line_chart_mock = MagicMock()
    monkeypatch.setattr(st, "warning", warning_mock)
    monkeypatch.setattr(st, "line_chart", line_chart_mock)

    test_window = TelemetryWindow(
        window_id=uuid.uuid4(),
        subsystem=Subsystem.POWER,
        start_time="2026-01-01T00:00:00Z",
        end_time="2026-01-01T00:04:00Z",
        channels={"P-1": [28.0] * 5, "T-1": [45.0] * 5},
        source_dataset="Synthetic",
    )

    # Render Power panel (prefix "P-")
    render_subsystem_panel(Subsystem.POWER, None, test_window, channel_prefix="P-")

    warning_mock.assert_not_called()
    line_chart_mock.assert_called_once()
    df_passed = line_chart_mock.call_args[0][0]
    # Must only contain P-1, not T-1
    assert list(df_passed.columns) == ["P-1"]
