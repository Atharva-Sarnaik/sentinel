"""
tests.unit.test_channel_mapping
================================
Channel alignment tests ensuring specialist YAML configs use canonical
SMAP channel IDs from libs/config/channel_map.yaml (ADR-0001).

Owner:   Sujal Hede (@Sujalhede)
Tier:    0 / 1 (tasks T0.4, T1.3, T1.5)
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import pytest
import yaml

from libs.config.loader import load_config
from libs.contracts import Subsystem, TelemetryWindow
from services.specialists.lstm_ae_template import LSTMAETemplate

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SPECIALIST_CONFIG_DIR = Path("services/specialists/configs")

# Canonical channel sets — these MUST match channel_map.yaml and ADR-0001.
CANONICAL = {
    "power": ["P-1", "P-2", "P-3", "P-4"],
    "thermal": ["T-1", "T-2", "T-3"],
    "attitude": ["A-1", "A-2", "A-3", "A-4"],
    "communications": ["C-1", "C-2", "D-1"],
}

ALL_CANONICAL_CHANNELS = sorted(ch for chs in CANONICAL.values() for ch in chs)

# Total count: 4 + 3 + 4 + 3 = 14
TOTAL_CANONICAL = 14


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_specialist_yaml(subsystem: str) -> dict:
    path = SPECIALIST_CONFIG_DIR / f"{subsystem}.yaml"
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _make_window(channels: dict[str, list[float]], seq_len: int = 30) -> TelemetryWindow:
    """Build a minimal TelemetryWindow for testing."""
    t0 = datetime(2024, 1, 1, tzinfo=UTC)
    return TelemetryWindow(
        subsystem=Subsystem.POWER,
        start_time=t0,
        end_time=t0 + timedelta(seconds=seq_len - 1),
        channels=channels,
        source_dataset="TEST",
    )


# ---------------------------------------------------------------------------
# Test 1: canonical channels in config match expected values
# ---------------------------------------------------------------------------


def test_canonical_channels_match_config_yaml() -> None:
    """load_config() returns the exact SMAP canonical channels from ADR-0001."""
    cfg = load_config()
    assert cfg.channel_map.power == CANONICAL["power"]
    assert cfg.channel_map.thermal == CANONICAL["thermal"]
    assert cfg.channel_map.attitude == CANONICAL["attitude"]
    assert cfg.channel_map.communications == CANONICAL["communications"]


# ---------------------------------------------------------------------------
# Test 2: specialist YAMLs align with canonical channel map
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("subsystem", ["power", "thermal", "attitude", "communications"])
def test_specialist_yaml_channels_match_canonical(subsystem: str) -> None:
    """Each specialist YAML must list exactly the canonical channels for its subsystem."""
    cfg = _load_specialist_yaml(subsystem)
    yaml_channels = sorted(cfg.get("channels", []))
    expected = sorted(CANONICAL[subsystem])
    assert yaml_channels == expected, (
        f"Specialist config '{subsystem}.yaml' channels {yaml_channels} "
        f"do not match canonical {expected}"
    )


# ---------------------------------------------------------------------------
# Test 3: _window_to_array raises on missing channel
# ---------------------------------------------------------------------------


def test_window_to_array_raises_on_missing_channel() -> None:
    """A window lacking a required channel must raise KeyError, not fill zeros."""
    config = {
        "subsystem": "power",
        "channels": ["P-1", "P-2"],
        "model": {"lstm_hidden_size": 16, "lstm_num_layers": 1, "latent_dim": 8},
    }
    model = LSTMAETemplate(config)

    # Window with WRONG channel names (mock names, not canonical)
    bad_window = _make_window({"P_BUS_VOLTAGE": [1.0] * 30, "P_BUS_CURRENT": [2.0] * 30})
    with pytest.raises(KeyError, match="P-1"):
        model._window_to_array(bad_window)


# ---------------------------------------------------------------------------
# Test 4: no silent zero filling
# ---------------------------------------------------------------------------


def test_window_to_array_no_silent_zero_fill() -> None:
    """_window_to_array must populate the matrix from actual channel data,
    not from a zero-filled default.

    This test directly inspects the array returned by _window_to_array
    to ensure the channel values are propagated (not silently zeroed).
    The companion test (test_window_to_array_raises_on_missing_channel)
    ensures that absent channels raise KeyError.
    """
    config = {
        "subsystem": "power",
        "channels": ["P-1"],
        "model": {"lstm_hidden_size": 16, "lstm_num_layers": 1, "latent_dim": 8},
    }
    model = LSTMAETemplate(config)

    # Build a window with a known non-zero signal
    signal = [float(j + 1) for j in range(30)]  # [1.0, 2.0, ..., 30.0]
    window = _make_window({"P-1": signal})

    arr = model._window_to_array(window)
    assert arr.shape == (30, 1)

    # The returned matrix must contain the actual signal, NOT zeros
    np.testing.assert_allclose(arr[:, 0], signal, rtol=1e-5)
    assert not np.allclose(arr, 0.0), (
        "Matrix is all zeros — _window_to_array is silently zero-filling "
        "instead of reading channel data."
    )


# ---------------------------------------------------------------------------
# Test 5: correct canonical channel ordering
# ---------------------------------------------------------------------------


def test_window_to_array_correct_channel_order() -> None:
    """Columns in the matrix must follow sorted channel order."""
    config = {
        "subsystem": "power",
        "channels": ["P-2", "P-1"],  # deliberately unsorted in config
        "model": {"lstm_hidden_size": 16, "lstm_num_layers": 1, "latent_dim": 8},
    }
    model = LSTMAETemplate(config)

    # channels are sorted at __init__
    assert model.channels == ["P-1", "P-2"]

    window = _make_window({"P-1": [1.0] * 30, "P-2": [2.0] * 30})
    arr = model._window_to_array(window)

    # Column 0 should be P-1 (value 1.0), column 1 should be P-2 (value 2.0)
    np.testing.assert_allclose(arr[:, 0], 1.0)
    np.testing.assert_allclose(arr[:, 1], 2.0)


# ---------------------------------------------------------------------------
# Test 6: all 14 canonical channels are registered
# ---------------------------------------------------------------------------


def test_all_canonical_channels_registered() -> None:
    """The canonical config must have exactly 14 channels across 4 subsystems."""
    cfg = load_config()
    assert len(cfg.channel_map.all_channels) == TOTAL_CANONICAL
    assert sorted(cfg.channel_map.all_channels) == ALL_CANONICAL_CHANNELS


# ---------------------------------------------------------------------------
# Test 7: subsystem_for lookup correctness
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "channel,expected_subsystem",
    [
        ("P-1", Subsystem.POWER),
        ("P-4", Subsystem.POWER),
        ("T-1", Subsystem.THERMAL),
        ("T-3", Subsystem.THERMAL),
        ("A-1", Subsystem.ATTITUDE),
        ("A-4", Subsystem.ATTITUDE),
        ("C-1", Subsystem.COMMUNICATIONS),
        ("C-2", Subsystem.COMMUNICATIONS),
        ("D-1", Subsystem.COMMUNICATIONS),
    ],
)
def test_subsystem_for_known_channel(channel: str, expected_subsystem: Subsystem) -> None:
    """subsystem_for() must return the correct subsystem for every canonical channel."""
    cfg = load_config()
    assert cfg.channel_map.subsystem_for(channel) == expected_subsystem


def test_subsystem_for_unknown_channel() -> None:
    """subsystem_for() returns None for channels not in the canonical map."""
    cfg = load_config()
    assert cfg.channel_map.subsystem_for("NONEXISTENT") is None
