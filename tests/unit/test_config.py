"""
tests.unit.test_config
======================
Unit tests for libs.config.loader (Task T0.4).

Owner:   Sujal Hede (@Sujalhede) / Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    0 (task T0.4)
Status:  complete — validates YAML parsing and SubsystemChannelMap helpers.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from libs.config.loader import SentinelConfig, SubsystemChannelMap, load_config
from libs.contracts.models import Subsystem


def test_load_default_config() -> None:
    """Test loading the bundled channel_map.yaml."""
    cfg = load_config()
    assert isinstance(cfg, SentinelConfig)
    assert cfg.project_name == "Sentinel"
    assert cfg.data.dataset == "SMAP"
    assert cfg.model.lstm_hidden_size == 64
    assert cfg.llm.max_retries == 2


def test_channel_map_helpers() -> None:
    """Test channel lookup and subsystem reverse-lookup."""
    cmap = SubsystemChannelMap(
        power=["P_BUS_VOLTAGE", "P_BUS_CURRENT"],
        thermal=["T_PANEL_A"],
        attitude=["A_GYRO_X"],
        communications=["C_TX_POWER"],
    )
    assert cmap.channels_for(Subsystem.POWER) == ["P_BUS_VOLTAGE", "P_BUS_CURRENT"]
    assert cmap.channels_for("thermal") == ["T_PANEL_A"]
    assert cmap.subsystem_for("P_BUS_VOLTAGE") == Subsystem.POWER
    assert cmap.subsystem_for("T_PANEL_A") == Subsystem.THERMAL
    assert cmap.subsystem_for("NONEXISTENT") is None
    assert len(cmap.all_channels) == 5


def test_load_custom_config() -> None:
    """Test loading from a temporary custom YAML file."""
    yaml_content = """
    project_name: "Sentinel-Custom"
    data:
      dataset: "MSL"
      window_size: 50
    channel_map:
      power:
        - "P_CUSTOM_VOLT"
    """
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as tf:
        tf.write(yaml_content)
        temp_path = Path(tf.name)

    try:
        cfg = load_config(temp_path)
        assert cfg.project_name == "Sentinel-Custom"
        assert cfg.data.dataset == "MSL"
        assert cfg.data.window_size == 50
        assert "P_CUSTOM_VOLT" in cfg.channel_map.power
    finally:
        temp_path.unlink(missing_ok=True)


def test_load_nonexistent_config_raises() -> None:
    """Test that pointing to a nonexistent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_config(Path("does_not_exist.yaml"))
