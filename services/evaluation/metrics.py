"""
services.evaluation.metrics
=============================
Event-wise precision, recall, F1, detection latency, and attribution accuracy.

Design rule (ADR-0002):
  • Headline metrics: event-wise P/R/F1, detection latency,
    subsystem attribution accuracy, ungrounded-statement rate.
  • Point-adjusted scores may be reported only as a labelled comparison.

Owner:   Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    4 (task T4.1)
Status:  not started
"""

from __future__ import annotations

from collections.abc import Sequence


def event_wise_precision_recall_f1(
    y_true_events: Sequence[tuple[int, int]],
    y_pred_events: Sequence[tuple[int, int]],
) -> dict[str, float]:
    """
    Compute event-wise precision, recall, and F1.

    Args:
        y_true_events: Ground-truth anomaly events as (start, end) index pairs.
        y_pred_events: Predicted anomaly events as (start, end) index pairs.

    Returns:
        dict with keys 'precision', 'recall', 'f1'.

    Raises:
        NotImplementedError: Implementation pending task T4.1.
    """
    # TODO (T4.1): implement event-wise metrics.
    raise NotImplementedError("event_wise_precision_recall_f1: pending task T4.1.")


def detection_latency(
    y_true_events: Sequence[tuple[int, int]],
    y_pred_events: Sequence[tuple[int, int]],
) -> float:
    """
    Compute mean detection latency (in time steps) across matched events.

    Raises:
        NotImplementedError: Implementation pending task T4.1.
    """
    # TODO (T4.1): implement latency metric.
    raise NotImplementedError("detection_latency: pending task T4.1.")


def subsystem_attribution_accuracy(
    y_true_subsystems: Sequence[str],
    y_pred_subsystems: Sequence[str],
) -> float:
    """
    Compute fraction of correctly attributed subsystems.

    Raises:
        NotImplementedError: Implementation pending task T4.1.
    """
    # TODO (T4.1): implement attribution accuracy.
    raise NotImplementedError("subsystem_attribution_accuracy: pending task T4.1.")


def ungrounded_statement_rate(
    total_explanations: int,
    ungrounded_count: int,
) -> float:
    """
    Compute ungrounded-statement rate = ungrounded_count / total_explanations.

    Raises:
        NotImplementedError: Implementation pending task T4.1.
    """
    # TODO (T4.1): implement ungrounded-statement rate.
    raise NotImplementedError("ungrounded_statement_rate: pending task T4.1.")
