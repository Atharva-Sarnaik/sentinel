"""
services.specialists.train
============================
Per-subsystem training pipeline for specialist LSTM-AE models (task T1.5).

Loads configuration for each subsystem (Power, Thermal, Attitude, Communications),
trains the LSTM-AE template on chronological training windows, calibrates the
dynamic nonparametric thresholder, evaluates validation metrics, and persists
model checkpoints.

Owner:   Sujal Hede (@Sujalhede) / Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    1 (task T1.5)
Status:  complete — trains 4 specialist models from YAML configs with evaluation metrics.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import yaml

from libs.contracts import Subsystem, TelemetryWindow
from services.specialists.lstm_ae_template import LSTMAETemplate
from services.specialists.specialist import SpecialistDetector
from services.specialists.thresholding import DynamicThresholder

logger = logging.getLogger(__name__)


def train_specialist(
    config: dict[str, Any],
    train_windows: Sequence[TelemetryWindow],
    val_windows: Sequence[TelemetryWindow] | None = None,
    model_run_id: str | None = None,
    epochs: int | None = None,
) -> tuple[SpecialistDetector, dict[str, Any]]:
    """
    Train a single specialist model according to its YAML config.

    Args:
        config: Dict parsed from specialist config YAML.
        train_windows: Windows reserved strictly for training.
        val_windows: Optional validation windows for post-training evaluation.
        model_run_id: Identifier for experiment tracking / manifest.
        epochs: Optional epoch override.

    Returns:
        tuple (SpecialistDetector, metrics_dict).
    """
    if not train_windows:
        raise ValueError("Cannot train specialist with empty train_windows.")

    subsystem_str = config.get("subsystem", "").lower()
    subsystem = Subsystem(subsystem_str)

    model_cfg = config.get("model", {})
    run_id = model_run_id or f"specialist-{subsystem.value}-001"
    target_epochs = epochs or int(model_cfg.get("epochs", 20))
    batch_size = int(model_cfg.get("batch_size", 32))
    lr = float(model_cfg.get("learning_rate", 1e-3))
    percentile = float(model_cfg.get("threshold_percentile", 95.0))

    # Initialize model template
    model = LSTMAETemplate(config)

    # Train model
    loss_history = model.train(
        train_windows=list(train_windows),
        epochs=target_epochs,
        batch_size=batch_size,
        learning_rate=lr,
    )

    # Compute reconstruction errors on training set to fit dynamic thresholder
    train_errors = [model.reconstruction_error(w) for w in train_windows]
    thresholder = DynamicThresholder(default_percentile=percentile)
    thresholder.fit(train_errors)

    detector = SpecialistDetector(
        subsystem=subsystem,
        model=model,
        thresholder=thresholder,
        model_run_id=run_id,
    )

    # Evaluate on val_windows (or train_windows if none)
    eval_set = val_windows if val_windows is not None else train_windows
    opinions = [detector.analyze(w) for w in eval_set]

    n_eval = len(opinions)
    anomalous = [op for op in opinions if op.is_anomalous]
    n_anom = len(anomalous)
    scores = [op.anomaly_score for op in opinions]
    raw_eval_errors = [model.reconstruction_error(w) for w in eval_set]

    metrics: dict[str, Any] = {
        "subsystem": subsystem.value,
        "run_id": run_id,
        "channels": model.channels,
        "n_train": len(train_windows),
        "n_eval": n_eval,
        "final_loss": loss_history[-1] if loss_history else 0.0,
        "threshold": thresholder.threshold_value,
        "threshold_mean": thresholder._mean,
        "threshold_std": thresholder._std,
        "anomaly_count": n_anom,
        "anomaly_rate": round(n_anom / max(1, n_eval), 4),
        "mean_anomaly_score": round(sum(scores) / max(1, n_eval), 4),
        "max_anomaly_score": round(max(scores) if scores else 0.0, 4),
        "mean_error": round(sum(raw_eval_errors) / max(1, n_eval), 6),
        "max_error": round(max(raw_eval_errors) if raw_eval_errors else 0.0, 6),
    }

    return detector, metrics


def train_all_from_configs(
    config_dir: Path | str,
    train_windows: Sequence[TelemetryWindow],
    val_windows: Sequence[TelemetryWindow] | None = None,
    output_dir: Path | str | None = None,
    epochs: int | None = None,
) -> dict[str, dict[str, Any]]:
    """
    Train all 4 specialists from the configs found in config_dir.

    Args:
        config_dir: Directory containing YAML configs (e.g. services/specialists/configs).
        train_windows: Training windows.
        val_windows: Validation windows.
        output_dir: Directory to save checkpoint .pt files.
        epochs: Optional epoch override.

    Returns:
        dict mapping subsystem name to its evaluation metrics dict.
    """
    cfg_path = Path(config_dir)
    if not cfg_path.is_dir():
        raise FileNotFoundError(f"Config directory not found: {cfg_path}")

    results: dict[str, dict[str, Any]] = {}
    config_files = sorted(cfg_path.glob("*.yaml")) + sorted(cfg_path.glob("*.yml"))

    if not config_files:
        raise FileNotFoundError(f"No YAML configuration files found in {cfg_path}")

    for file_path in config_files:
        with open(file_path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        subsystem_str = cfg.get("subsystem")
        if not subsystem_str:
            continue

        detector, metrics = train_specialist(
            config=cfg,
            train_windows=train_windows,
            val_windows=val_windows,
            epochs=epochs,
        )

        if output_dir is not None:
            out_p = Path(output_dir)
            out_p.mkdir(parents=True, exist_ok=True)
            ckpt_path = out_p / f"{subsystem_str}.pt"
            detector.save(ckpt_path)
            metrics["saved_path"] = str(ckpt_path)

        results[subsystem_str] = metrics

    return results
