"""
libs.config.loader
==================
Validates and exposes the Sentinel YAML configuration.

Design: a single SentinelConfig object is the runtime source of truth.
        Services import this; they never read YAML files directly.

Status: scaffolding — Pydantic model and loader stub only.
        Implementation (actual YAML parsing + validation) not started.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Config schema
# ---------------------------------------------------------------------------


class SubsystemChannelMap(BaseModel):
    """Maps subsystem names to their telemetry channel identifiers.

    Risk R1: the correctness of this grouping is unverified (task T0.5).
    ADR-0001 records the final dataset decision.
    """

    model_config = ConfigDict(extra="allow")

    power: list[str] = Field(default_factory=list)
    thermal: list[str] = Field(default_factory=list)
    attitude: list[str] = Field(default_factory=list)
    communications: list[str] = Field(default_factory=list)


class DataConfig(BaseModel):
    dataset: str = "SMAP"  # or MSL, ESA-ADB, OPS-SAT
    replay_path: Path = Path("data/raw")
    window_size: int = 100  # time steps
    stride: int = 10
    test_fraction: float = 0.2  # chronological split ratio


class ModelConfig(BaseModel):
    lstm_hidden_size: int = 64
    lstm_num_layers: int = 2
    latent_dim: int = 32
    epochs: int = 50
    batch_size: int = 64
    learning_rate: float = 1e-3
    threshold_percentile: float = 95.0


class LLMConfig(BaseModel):
    provider: str = "openai"
    model_name: str = "gpt-4o-mini"
    max_retries: int = 2  # verifier retry budget (ADR-0002)
    temperature: float = 0.0
    max_tokens: int = 512


class SentinelConfig(BaseModel):
    """Top-level configuration container.

    Loaded once at startup; treat as read-only after construction.
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
        NotImplementedError: Full config merging is not yet implemented.
                             Only the channel map stub is loaded.
    """
    config_path = path or _DEFAULT_CONFIG_PATH

    with config_path.open() as fh:
        _raw: dict[str, Any] = yaml.safe_load(fh) or {}

    # TODO (T0.4): merge per-service YAML files; validate all fields.
    raise NotImplementedError(
        "load_config: full implementation pending task T0.4. "
        f"Config path resolved to: {config_path}"
    )
