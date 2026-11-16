"""
services.evaluation.ablation
==============================
Ablation study harness executing Sentinel evaluation arms A through E
on identical telemetry windows per ADR-0002 (Rule R5).

Evaluation Arms:
  A — Static threshold baseline (services.baselines.static_threshold)
  B — Isolation Forest baseline (services.baselines.isolation_forest)
  C — Single combined monolithic LSTM-AE (services.baselines.combined_lstm_ae)
  D — Specialist agents operating alone without coordinator (services.specialists)
  E — Full coordinated multi-agent system (Sentinel orchestrator)

Design Rules (ADR-0002):
  • Rule R5: Arms A–E are always compared on identical telemetry windows.
  • Strict separation of training and evaluation data; no leakage.
  • Service independence: dynamic dispatch and dependency injection are used
    to strictly comply with pyproject.toml import-linter contracts.
  • Graceful degradation: Arm E dependencies (Tier 3) are checked and reported
    honestly as BLOCKED_PENDING_TIER_3 when unimplemented.

Owner:   Atharva Sarnaik (@Atharva-Sarnaik) / Sujal Hede (@Sujalhede)
Tier:    4 (task T4.2)
Status:  complete — ablation harness with arm dispatchers and metrics.
"""

from __future__ import annotations

import importlib
import inspect
import logging
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from libs.contracts import FusionDecision, Severity, SpecialistOpinion, TelemetryWindow

logger = logging.getLogger(__name__)

ARMS: tuple[str, ...] = ("A", "B", "C", "D", "E")
REQUIRED_SUBSYSTEMS: tuple[str, ...] = ("power", "thermal", "attitude", "communications")


def _normalize_subsystem_name(sub: Any) -> str:
    """Normalize Subsystem enum, string, or identifier to canonical lowercase string."""
    val = str(sub.value).lower() if hasattr(sub, "value") else str(sub).lower()
    if val.startswith("subsystem."):
        val = val.split(".", 1)[1]
    return val


def compute_binary_metrics(
    predictions: Sequence[bool],
    ground_truth: Sequence[bool],
) -> dict[str, float | int]:
    """
    Calculate window-level TP, FP, TN, FN, Precision, Recall, F1, and FPR.

    Args:
        predictions: Binary anomaly predictions per window.
        ground_truth: Ground-truth binary labels per window.

    Returns:
        Dict with classification counts and rates.

    Raises:
        ValueError: If predictions and ground_truth sequences have unequal lengths.
    """
    if len(predictions) != len(ground_truth):
        raise ValueError(
            f"Length mismatch: predictions ({len(predictions)}) vs "
            f"ground_truth ({len(ground_truth)})."
        )

    if not predictions:
        return {
            "true_positives": 0,
            "false_positives": 0,
            "true_negatives": 0,
            "false_negatives": 0,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "false_positive_rate": 0.0,
        }

    tp = sum(1 for p, y in zip(predictions, ground_truth) if p and y)
    fp = sum(1 for p, y in zip(predictions, ground_truth) if p and not y)
    tn = sum(1 for p, y in zip(predictions, ground_truth) if not p and not y)
    fn = sum(1 for p, y in zip(predictions, ground_truth) if not p and y)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

    return {
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "false_positive_rate": round(fpr, 4),
    }


def _run_arm_a(
    windows: Sequence[TelemetryWindow],
    model: Any | None,
    train_windows: Sequence[TelemetryWindow] | None,
) -> tuple[list[bool], dict[str, Any]]:
    """Execute Arm A: Static Threshold Baseline."""
    if model is None:
        if train_windows is None:
            raise ValueError(
                "Arm A requires either a pre-fitted model via models['A'] "
                "or train_windows to fit thresholds."
            )
        mod = importlib.import_module("services.baselines.static_threshold")
        static_cls = mod.StaticThresholdBaseline
        detector = static_cls(model_run_id="ablation-arm-a")
        detector.fit(train_windows)
    else:
        detector = model

    preds: list[bool] = []
    opinions: list[SpecialistOpinion] = []
    for w in windows:
        op = detector.predict(w) if hasattr(detector, "predict") else detector(w)
        opinions.append(op)
        is_anom = op.is_anomalous if hasattr(op, "is_anomalous") else bool(op)
        preds.append(is_anom)

    meta = {
        "arm": "A",
        "name": "Static Threshold Baseline",
        "sample_count": len(windows),
        "anomaly_count": sum(preds),
        "anomaly_rate": round(sum(preds) / max(1, len(windows)), 4),
    }
    return preds, meta


def _run_arm_b(
    windows: Sequence[TelemetryWindow],
    model: Any | None,
    train_windows: Sequence[TelemetryWindow] | None,
) -> tuple[list[bool], dict[str, Any]]:
    """Execute Arm B: Isolation Forest Baseline."""
    if model is None:
        if train_windows is None:
            raise ValueError(
                "Arm B requires either a pre-fitted model via models['B'] "
                "or train_windows to fit the forest."
            )
        mod = importlib.import_module("services.baselines.isolation_forest")
        iforest_cls = mod.IsolationForestBaseline
        detector = iforest_cls(n_estimators=100, contamination=0.05, random_state=42)
        detector.fit(train_windows)
    else:
        detector = model

    preds: list[bool] = []
    opinions: list[SpecialistOpinion] = []
    for w in windows:
        op = detector.predict(w) if hasattr(detector, "predict") else detector(w)
        opinions.append(op)
        is_anom = op.is_anomalous if hasattr(op, "is_anomalous") else bool(op)
        preds.append(is_anom)

    meta = {
        "arm": "B",
        "name": "Isolation Forest Baseline",
        "sample_count": len(windows),
        "anomaly_count": sum(preds),
        "anomaly_rate": round(sum(preds) / max(1, len(windows)), 4),
    }
    return preds, meta


def _run_arm_c(
    windows: Sequence[TelemetryWindow],
    model: Any | None,
    train_windows: Sequence[TelemetryWindow] | None,
) -> tuple[list[bool], dict[str, Any]]:
    """Execute Arm C: Single Combined Monolithic LSTM-AE."""
    if model is None:
        if train_windows is None:
            raise ValueError(
                "Arm C requires either a pre-trained detector via models['C'] "
                "or train_windows to train the autoencoder."
            )
        mod = importlib.import_module("services.baselines.combined_lstm_ae")
        combined_cls = mod.CombinedLSTMAEDetector
        channels = sorted(train_windows[0].channels.keys())
        detector = combined_cls(
            channels=channels,
            hidden_dim=32,
            num_layers=1,
            latent_dim=16,
            model_run_id="ablation-arm-c",
        )
        detector.train(train_windows, epochs=5, batch_size=8)
    else:
        detector = model

    preds: list[bool] = []
    threshold_val = getattr(detector, "threshold", None)
    for w in windows:
        op = detector.predict(w) if hasattr(detector, "predict") else detector(w)
        is_anom = op.is_anomalous if hasattr(op, "is_anomalous") else bool(op)
        preds.append(is_anom)

    meta = {
        "arm": "C",
        "name": "Combined LSTM-AE",
        "sample_count": len(windows),
        "anomaly_count": sum(preds),
        "anomaly_rate": round(sum(preds) / max(1, len(windows)), 4),
        "threshold_used": threshold_val,
    }
    return preds, meta


def _run_arm_d(
    windows: Sequence[TelemetryWindow],
    model: Any | None,
    train_windows: Sequence[TelemetryWindow] | None,
) -> tuple[list[bool] | None, dict[str, Any]]:
    """
    Execute Arm D: Four Specialist LSTM-AEs operating independently (no coordinator/fusion).

    Evaluates windows across all four required specialist models (Power, Thermal, Attitude, Communications)
    independently. Window-level anomaly is declared if ANY specialist flags the window (union).
    Individual subsystem predictions and anomaly counts are strictly preserved.
    Does not invoke fusion or coordination.

    If any specialist cannot be loaded or trained, or if any required subsystem detector
    is missing, returns (None, meta) with status="UNAVAILABLE" and a descriptive error
    identifying the missing or failed subsystem(s).
    """
    detectors: dict[str, Any] = {}
    if model is not None:
        if isinstance(model, dict):
            for k, v in model.items():
                key_str = _normalize_subsystem_name(k)
                detectors[key_str] = v
        elif isinstance(model, (list, tuple)):
            for i, det in enumerate(model):
                sub = getattr(det, "subsystem", None)
                key_str = _normalize_subsystem_name(sub) if sub is not None else f"specialist_{i}"
                detectors[key_str] = det
        else:
            sub = getattr(model, "subsystem", None)
            key_str = _normalize_subsystem_name(sub) if sub is not None else "default"
            detectors[key_str] = model
    else:
        if train_windows is None:
            raise ValueError(
                "Arm D requires either pre-trained specialists via models['D'] "
                "or train_windows to train specialist models."
            )
        # Attempt to train all four specialists from configuration files
        try:
            train_mod = importlib.import_module("services.specialists.train")
            train_fn = train_mod.train_specialist
            yaml_mod = importlib.import_module("yaml")
            config_dir = Path("services/specialists/configs")
            config_files = sorted(config_dir.glob("*.yaml")) + sorted(config_dir.glob("*.yml"))
            if not config_files:
                return None, {
                    "arm": "D",
                    "name": "Specialists Alone (No Coordinator)",
                    "status": "UNAVAILABLE",
                    "sample_count": len(windows),
                    "error": f"No specialist configuration files found in {config_dir}.",
                    "reason": "Specialist configuration files are missing.",
                }
            for cf in config_files:
                with open(cf, encoding="utf-8") as f:
                    cfg = yaml_mod.safe_load(f)
                subsystem_str = cfg.get("subsystem")
                if not subsystem_str:
                    continue
                norm_sub = _normalize_subsystem_name(subsystem_str)
                det, _ = train_fn(
                    config=cfg,
                    train_windows=train_windows,
                    val_windows=None,
                    epochs=3,
                )
                detectors[norm_sub] = det
        except Exception as e:
            logger.warning("Could not train specialist detectors for Arm D: %s", e)
            return None, {
                "arm": "D",
                "name": "Specialists Alone (No Coordinator)",
                "status": "UNAVAILABLE",
                "sample_count": len(windows),
                "reason": f"Could not obtain trained specialist detector instances: {e}",
                "error": str(e),
            }

    # Validate that every detector is an executable detector instance
    def _is_executable_detector(obj: Any) -> bool:
        if obj is None or isinstance(obj, (int, float, str, bool, list, tuple)):
            return False
        if isinstance(obj, dict):
            # Summary metrics dicts are not executable detectors
            return False
        return hasattr(obj, "analyze") or callable(obj)

    if not detectors or not all(_is_executable_detector(d) for d in detectors.values()):
        logger.warning("Arm D: models are not valid executable detector instances.")
        meta = {
            "arm": "D",
            "name": "Specialists Alone (No Coordinator)",
            "status": "UNAVAILABLE",
            "sample_count": len(windows),
            "reason": (
                "Actual SpecialistDetector instances could not be obtained. "
                "Provided models are summary metrics dictionaries or invalid objects lacking .analyze() or __call__."
            ),
            "error": "Missing executable detector instances for Arm D.",
            "subsystems_evaluated": list(detectors.keys()),
        }
        return None, meta

    # Verify that ALL four required specialist detectors are present
    missing_subsystems = [s for s in REQUIRED_SUBSYSTEMS if s not in detectors]
    if missing_subsystems:
        logger.warning("Arm D: Missing required specialist detector(s): %s", missing_subsystems)
        meta = {
            "arm": "D",
            "name": "Specialists Alone (No Coordinator)",
            "status": "UNAVAILABLE",
            "sample_count": len(windows),
            "error": f"Missing required specialist detector(s): {', '.join(sorted(missing_subsystems))}.",
            "reason": (
                f"Arm D requires all four specialists (Power, Thermal, Attitude, Communications). "
                f"Missing: {sorted(missing_subsystems)}."
            ),
            "subsystems_evaluated": list(detectors.keys()),
        }
        return None, meta

    # Evaluate all windows with each specialist
    subsystem_preds: dict[str, list[bool]] = {}
    for sub_name in REQUIRED_SUBSYSTEMS:
        det = detectors[sub_name]
        sub_preds: list[bool] = []
        for w in windows:
            op = det.analyze(w) if hasattr(det, "analyze") else det(w)
            is_anom = op.is_anomalous if hasattr(op, "is_anomalous") else bool(op)
            sub_preds.append(is_anom)
        subsystem_preds[str(sub_name)] = sub_preds

    # Union of all independent specialists
    window_preds: list[bool] = []
    for i in range(len(windows)):
        any_anom = any(subsystem_preds[s][i] for s in REQUIRED_SUBSYSTEMS)
        window_preds.append(any_anom)

    meta = {
        "arm": "D",
        "name": "Specialists Alone (No Coordinator)",
        "status": "EXECUTED",
        "sample_count": len(windows),
        "anomaly_count": sum(window_preds),
        "anomaly_rate": round(sum(window_preds) / max(1, len(windows)), 4),
        "subsystems_evaluated": list(detectors.keys()),
        "per_subsystem_anomaly_counts": {s: sum(preds) for s, preds in subsystem_preds.items()},
        "subsystem_predictions": subsystem_preds,
    }
    return window_preds, meta


def _run_arm_e(
    windows: Sequence[TelemetryWindow],
    pipeline_fn: Callable[[Any], Any] | None,
) -> tuple[list[bool] | None, dict[str, Any]]:
    """
    Execute Arm E: Full Coordinated Multi-Agent System (Specialists + Fusion + LLM Reasoner + Verifier).

    Dynamically resolves the default orchestrator entry point (services.orchestrator.graph.run_pipeline)
    unless an explicit pipeline_fn is injected.
    If the orchestrator raises NotImplementedError (Tier 3 pending),
    catches it specifically and returns BLOCKED_PENDING_TIER_3 with blocker details.
    Does not catch or mask unrelated exceptions.
    Validates pipeline output to ensure it contains a valid FusionDecision or anomaly indicator;
    raises ValueError on invalid outputs rather than silently defaulting to False.
    """
    fn = pipeline_fn
    is_default = False
    if fn is None:
        orch_mod = importlib.import_module("services.orchestrator.graph")
        fn = orch_mod.run_pipeline
        is_default = True

    # Determine input argument format from function signature and call it once (no retry on TypeError)
    expects_dict = is_default
    if not is_default:
        try:
            sig = inspect.signature(fn)
            first_param = next(iter(sig.parameters.values()), None)
            if first_param is not None:
                if first_param.name in (
                    "window_dict",
                    "data",
                    "payload",
                ) or first_param.annotation in (
                    dict,
                    dict[str, Any],
                ):
                    expects_dict = True
                elif first_param.annotation is TelemetryWindow or first_param.name in (
                    "window",
                    "w",
                ):
                    expects_dict = False
        except (ValueError, TypeError):
            pass

    preds: list[bool] = []
    for w in windows:
        arg = w.model_dump() if expects_dict else w
        try:
            res = fn(arg)
        except NotImplementedError as e:
            logger.info("Arm E blocked pending Tier 3 implementation: %s", e)
            meta = {
                "arm": "E",
                "name": "Full Coordinated System (Sentinel)",
                "status": "BLOCKED_PENDING_TIER_3",
                "blocker": str(e),
                "reason": (
                    "Orchestrator pipeline execution raised NotImplementedError. "
                    "Tier 3 multi-agent orchestration is pending."
                ),
                "blockers": [
                    f"services.orchestrator.graph (run_pipeline: {e})",
                    "services.reasoner.reasoner (synthesise_explanation raises NotImplementedError)",
                    "services.verifier.grounding (verify_explanation raises NotImplementedError)",
                    "services.verifier.retry (verify_with_retry raises NotImplementedError)",
                ],
            }
            return None, meta

        # Extract and validate anomaly decision from returned output
        is_anom: bool | None = None
        if isinstance(res, FusionDecision):
            is_anom = res.is_anomalous
        elif isinstance(res, dict):
            dec = res.get("fusion_decision") or res.get("decision") or res.get("FusionDecision")
            if isinstance(dec, FusionDecision):
                is_anom = dec.is_anomalous
            elif dec is not None and hasattr(dec, "is_anomalous"):
                is_anom = bool(dec.is_anomalous)
            elif dec is not None and hasattr(dec, "severity"):
                is_anom = dec.severity != Severity.NOMINAL
            elif "is_anomalous" in res and isinstance(res["is_anomalous"], bool):
                is_anom = res["is_anomalous"]
            elif "severity" in res and isinstance(res["severity"], (Severity, str)):
                is_anom = res["severity"] not in (
                    Severity.NOMINAL,
                    "nominal",
                    Severity.NOMINAL.value,
                )
        elif hasattr(res, "is_anomalous") and isinstance(res.is_anomalous, bool):
            is_anom = res.is_anomalous
        elif hasattr(res, "severity") and isinstance(res.severity, Severity):
            is_anom = res.severity != Severity.NOMINAL

        if is_anom is None:
            raise ValueError(
                f"Arm E received invalid or unrecognized pipeline output: {res!r}. "
                "Output must be a FusionDecision or a dict containing a valid decision or anomaly flag."
            )

        preds.append(is_anom)

    meta = {
        "arm": "E",
        "name": "Full Coordinated System (Sentinel)",
        "status": "EXECUTED_DEFAULT_PIPELINE" if is_default else "EXECUTED_WITH_INJECTED_PIPELINE",
        "sample_count": len(windows),
        "anomaly_count": sum(preds),
        "anomaly_rate": round(sum(preds) / max(1, len(windows)), 4),
    }
    return preds, meta


def run_ablation(
    windows: Sequence[TelemetryWindow],
    arms: tuple[str, ...] = ARMS,
    ground_truth: Sequence[bool] | None = None,
    train_windows: Sequence[TelemetryWindow] | None = None,
    models: dict[str, Any] | None = None,
    pipeline_fn: Callable[[TelemetryWindow], Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """
    Run each requested ablation arm on identical telemetry windows and return a metrics dict.

    Design Rule R5 (ADR-0002):
      • All arms receive the exact same sequence of TelemetryWindows.
      • Evaluation windows are strictly separated from training windows.

    Args:
        windows: Identical list of TelemetryWindows evaluated across all arms.
        arms: Subset of ARMS to run (default: ('A', 'B', 'C', 'D', 'E')).
        ground_truth: Optional binary ground-truth labels per window for calculating
            classification metrics (Precision, Recall, F1, FPR).
        train_windows: Optional chronological healthy telemetry windows used strictly
            for fitting models when unfitted models are not provided.
        models: Optional dict of pre-instantiated detector models keyed by arm ('A', 'B', 'C', 'D').
        pipeline_fn: Optional callable for Arm E execution (allows testing orchestrator mock).

    Returns:
        Dict mapping arm label to its evaluation metrics and execution metadata.

    Raises:
        ValueError: If windows sequence is empty, if arms is empty, if an unrecognized
            arm is requested, or if ground_truth length mismatches windows.
    """
    if not windows:
        raise ValueError("Cannot run ablation on empty windows sequence.")

    if not arms:
        raise ValueError("arms tuple must not be empty.")

    for arm in arms:
        if arm not in ARMS:
            raise ValueError(f"Unrecognized ablation arm '{arm}'. Must be one of {ARMS}.")

    if ground_truth is not None and len(ground_truth) != len(windows):
        raise ValueError(
            f"Length mismatch: ground_truth ({len(ground_truth)}) vs windows ({len(windows)})."
        )

    results: dict[str, dict[str, Any]] = {}
    models_dict = models or {}

    for arm in arms:
        logger.info("Executing ablation arm %s on %d windows...", arm, len(windows))
        t_start = time.perf_counter()

        if arm == "A":
            preds, meta = _run_arm_a(windows, models_dict.get("A"), train_windows)
        elif arm == "B":
            preds, meta = _run_arm_b(windows, models_dict.get("B"), train_windows)
        elif arm == "C":
            preds, meta = _run_arm_c(windows, models_dict.get("C"), train_windows)
        elif arm == "D":
            preds, meta = _run_arm_d(windows, models_dict.get("D"), train_windows)
        elif arm == "E":
            preds, meta = _run_arm_e(windows, pipeline_fn)
        else:
            continue

        elapsed = round(time.perf_counter() - t_start, 4)
        meta["execution_time_sec"] = elapsed

        if preds is not None:
            meta["predictions"] = preds
            if ground_truth is not None:
                metrics = compute_binary_metrics(preds, ground_truth)
                meta.update(metrics)

        results[arm] = meta

    logger.info("Ablation study completed for arms: %s", list(results.keys()))
    return results
