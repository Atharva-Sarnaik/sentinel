"""
libs.config.loader
==================
Validates and exposes the Sentinel YAML configuration.

Design: a single SentinelConfig object is the runtime source of truth.
        Services import this; they never read YAML files directly.

Status: complete — YAML parsing, schema validation, and channel mapping helpers (T0.4).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from libs.contracts.models import Subsystem

# ---------------------------------------------------------------------------
# Config schema
# ---------------------------------------------------------------------------


class SubsystemChannelMap(BaseModel):
    """Maps subsystem names to their telemetry channel identifiers.

    Risk R1: the correctness of this grouping is unverified (task T0.5).
    ADR-0001 records the final dataset decision.
    """

    model_config = ConfigDict(frozen=True, extra="allow")

    power: list[str] = Field(default_factory=list)
    thermal: list[str] = Field(default_factory=list)
    attitude: list[str] = Field(default_factory=list)
    communications: list[str] = Field(default_factory=list)

    def channels_for(self, subsystem: Subsystem | str) -> list[str]:
        """Return the list of channel names assigned to the given subsystem."""
        sub_name = str(subsystem).lower()
        if hasattr(self, sub_name):
            return getattr(self, sub_name)  # type: ignore[no-any-return]
        return []

    def subsystem_for(self, channel: str) -> Subsystem | None:
        """Find which subsystem a channel belongs to, or None if unmapped."""
        for sub in Subsystem:
            if channel in self.channels_for(sub):
                return sub
        return None

    @property
    def all_channels(self) -> list[str]:
        """Flattened list of all registered channels across all subsystems."""
        return self.power + self.thermal + self.attitude + self.communications


class DataConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    dataset: str = "SMAP"  # or MSL, ESA-ADB, OPS-SAT
    replay_path: Path = Path("data/raw")
    window_size: int = 100  # time steps
    stride: int = 10
    test_fraction: float = 0.2  # chronological split ratio


class ModelConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    lstm_hidden_size: int = 64
    lstm_num_layers: int = 2
    latent_dim: int = 32
    epochs: int = 50
    batch_size: int = 64
    learning_rate: float = 1e-3
    threshold_percentile: float = 95.0


class LLMConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    provider: str = "openai"
    model_name: str = "gpt-4o-mini"
    max_retries: int = 2  # verifier retry budget (ADR-0002)
    temperature: float = 0.0
    max_tokens: int = 512


class SentinelConfig(BaseModel):
    """Top-level configuration container.

    Loaded once at startup; treated as read-only after construction.
    """

    model_config = ConfigDict(frozen=True)

    project_name: str = "Sentinel"
    channel_map: SubsystemChannelMap = Field(default_factory=SubsystemChannelMap)
    data: DataConfig = Field(default_factory=DataConfig)
    model: ModelConfig = Field(default_factory=ModelConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    extra: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

_DEFAULT_CONFIG_PATH = Path(__file__).parent / "channel_map.yaml"


def load_config(path: Path | None = None) -> SentinelConfig:
    """Load and validate the Sentinel configuration from a YAML file.

    Args:
        path: Path to the YAML config file. Defaults to the bundled
              channel_map.yaml in this package directory.

    Returns:
        A validated, frozen SentinelConfig instance.

    Raises:
        FileNotFoundError: If the specified configuration file does not exist.
        ValueError: If YAML syntax is invalid or schema validation fails.
    """
    config_path = path or _DEFAULT_CONFIG_PATH

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with config_path.open(encoding="utf-8") as fh:
        raw: dict[str, Any] = yaml.safe_load(fh) or {}

    return SentinelConfig.model_validate(raw)
