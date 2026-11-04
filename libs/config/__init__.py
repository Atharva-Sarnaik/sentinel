"""
libs.config
===========
YAML configuration loader for Sentinel.

The channel→subsystem map (risk R1) is defined in channel_map.yaml.
All other configuration (thresholds, model hyperparameters) live in
per-service YAML files referenced from the top-level config.

Status: scaffolding — loader stub only, implementation not started.
"""

from libs.config.loader import SentinelConfig, load_config

__all__ = ["load_config", "SentinelConfig"]
