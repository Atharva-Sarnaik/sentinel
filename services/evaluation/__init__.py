"""services.evaluation — Metrics, ablation harness, golden set."""

from services.evaluation.ablation import ARMS, run_ablation
from services.evaluation.golden_set import GroundingGoldenExample, load_grounding_golden_set
from services.evaluation.metrics import (
    binary_to_events,
    detection_latency,
    event_wise_precision_recall_f1,
    events_to_binary,
    point_adjusted_precision_recall_f1,
    subsystem_attribution_accuracy,
    ungrounded_statement_rate,
)

__all__ = [
    "ARMS",
    "GroundingGoldenExample",
    "binary_to_events",
    "detection_latency",
    "event_wise_precision_recall_f1",
    "events_to_binary",
    "load_grounding_golden_set",
    "point_adjusted_precision_recall_f1",
    "run_ablation",
    "subsystem_attribution_accuracy",
    "ungrounded_statement_rate",
]
