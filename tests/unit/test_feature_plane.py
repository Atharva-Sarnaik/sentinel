"""
tests.unit.test_feature_plane
=============================
Unit tests for services.feature_plane (Task T0.9).

Owner:   Sujal Hede (@Sujalhede)
Tier:    0 (task T0.9)
Status:  complete — validates splits, normalisation, windowing, and feature extraction.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from libs.contracts import Subsystem, TelemetryWindow
from services.feature_plane.features import extract_features
from services.feature_plane.normalisation import ChannelNormaliser
from services.feature_plane.splits import chronological_split
from services.feature_plane.windowing import apply_sliding_window


@pytest.fixture
def series_of_windows() -> list[TelemetryWindow]:
    t0 = datetime(2024, 1, 1, 0, 0, tzinfo=UTC)
    windows = []
    for i in range(10):
        start = t0 + timedelta(minutes=i * 5)
        end = start + timedelta(minutes=4)
        windows.append(
            TelemetryWindow(
                subsystem=Subsystem.POWER,
                start_time=start,
                end_time=end,
                channels={"P-1": [10.0 + i] * 50, "P-2": [2.0 + i * 0.1] * 50},
                source_dataset="SMAP",
            )
        )
    return windows


def test_chronological_split(series_of_windows: list[TelemetryWindow]) -> None:
    train_w, test_w = chronological_split(series_of_windows, test_fraction=0.3)
    assert len(train_w) == 7
    assert len(test_w) == 3
    # Verify strict time boundary
    assert train_w[-1].end_time < test_w[0].start_time


def test_channel_normaliser(series_of_windows: list[TelemetryWindow]) -> None:
    train_w, test_w = chronological_split(series_of_windows, test_fraction=0.2)
    normaliser = ChannelNormaliser().fit(train_w)

    transformed_train = normaliser.transform(train_w[0])
    transformed_test = normaliser.transform(test_w[0])

    assert transformed_train.metadata.get("normalized") is True
    assert transformed_test.metadata.get("normalized") is True
    assert len(transformed_train.channels["P-1"]) == 50


def test_apply_sliding_window(series_of_windows: list[TelemetryWindow]) -> None:
    single_window = series_of_windows[0]
    subs = apply_sliding_window(single_window, window_size=20, stride=10)
    # (50 - 20) // 10 + 1 = 4
    assert len(subs) == 4
    for sub in subs:
        assert sub.window_length == 20
        assert sub.start_time < sub.end_time


def test_extract_features(series_of_windows: list[TelemetryWindow]) -> None:
    features = extract_features(series_of_windows[0])
    assert "P-1__mean" in features
    assert "P-1__std" in features
    assert "P-1__min" in features
    assert "P-1__max" in features
    assert "P-1__delta" in features
    assert features["P-1__mean"] == 10.0
