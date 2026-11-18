"""
services.evaluation.metrics
=============================
Event-wise precision, recall, F1, detection latency, and attribution accuracy.

Design rules (ADR-0002):
  • Rule R4: Headline metrics are event-wise precision/recall/F1,
    detection latency, subsystem attribution accuracy, and ungrounded-statement rate.
  • Point-adjusted scores may be reported only as a labelled comparison,
    never as the headline metric.

Owner:   Atharva Sarnaik (@Atharva-Sarnaik) / Sujal Hede (@Sujalhede)
Tier:    4 (task T4.1)
Status:  complete — validated event-wise, latency, attribution, and grounding metrics.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any


def _validate_event(event: Any) -> tuple[int, int]:
    """Validate that an event is a valid (start, end) index tuple."""
    if not isinstance(event, (tuple, list)) or len(event) != 2:
        raise ValueError(f"Event must be a 2-tuple (start, end), got: {event!r}")
    start, end = event
    if not isinstance(start, int) or isinstance(start, bool):
        raise ValueError(f"Event start must be an integer, got: {type(start).__name__}")
    if not isinstance(end, int) or isinstance(end, bool):
        raise ValueError(f"Event end must be an integer, got: {type(end).__name__}")
    if start < 0 or end < 0:
        raise ValueError(f"Event indices must be non-negative, got: ({start}, {end})")
    if start > end:
        raise ValueError(f"Event start ({start}) cannot exceed end ({end})")
    return int(start), int(end)


def _events_overlap(e1: tuple[int, int], e2: tuple[int, int]) -> bool:
    """Return True if two closed intervals [s1, e1] and [s2, e2] overlap."""
    return max(e1[0], e2[0]) <= min(e1[1], e2[1])


def binary_to_events(binary_sequence: Sequence[bool]) -> list[tuple[int, int]]:
    """
    Convert a sequence of boolean flags into contiguous (start, end) event index pairs.

    Args:
        binary_sequence: Chronological sequence of boolean anomaly flags.

    Returns:
        List of (start_idx, end_idx) tuples for contiguous True segments.
    """
    events: list[tuple[int, int]] = []
    in_event = False
    start_idx = 0

    for i, flag in enumerate(binary_sequence):
        if flag and not in_event:
            in_event = True
            start_idx = i
        elif not flag and in_event:
            in_event = False
            events.append((start_idx, i - 1))

    if in_event:
        events.append((start_idx, len(binary_sequence) - 1))

    return events


def events_to_binary(events: Sequence[tuple[int, int]], length: int) -> list[bool]:
    """
    Convert a list of (start, end) event index pairs into a boolean sequence.

    Args:
        events: Contiguous (start, end) index pairs.
        length: Desired length of the output boolean sequence.

    Returns:
        List of booleans of length `length` with True at all event indices.
    """
    if length < 0:
        raise ValueError(f"Length must be non-negative, got {length}")
    result = [False] * length
    for ev in events:
        s, e = _validate_event(ev)
        if e >= length:
            raise ValueError(f"Event end index ({e}) exceeds sequence length ({length})")
        for i in range(s, e + 1):
            result[i] = True
    return result


def event_wise_precision_recall_f1(
    y_true_events: Sequence[tuple[int, int]],
    y_pred_events: Sequence[tuple[int, int]],
    *,
    zero_division: float = 0.0,
) -> dict[str, float]:
    """
    Compute event-wise precision, recall, and F1.

    Matching criterion:
      - A true anomaly event is recalled if at least one predicted event overlaps with it.
      - A predicted anomaly event is precise if it overlaps with at least one true anomaly event.

    Args:
        y_true_events: Ground-truth anomaly events as (start, end) index pairs.
        y_pred_events: Predicted anomaly events as (start, end) index pairs.
        zero_division: Value returned when denominator is zero (default 0.0).

    Returns:
        dict with keys 'precision', 'recall', 'f1' rounded to 4 decimal places.

    Raises:
        ValueError: If any event interval is malformed or invalid.
    """
    valid_true = [_validate_event(ev) for ev in y_true_events]
    valid_pred = [_validate_event(ev) for ev in y_pred_events]

    if not valid_true and not valid_pred:
        return {
            "precision": float(zero_division),
            "recall": float(zero_division),
            "f1": float(zero_division),
        }

    # Recall: fraction of ground-truth events detected by at least one prediction
    tp_recall = sum(1 for t in valid_true if any(_events_overlap(t, p) for p in valid_pred))
    recall = tp_recall / len(valid_true) if valid_true else float(zero_division)

    # Precision: fraction of predicted events that overlap with a ground-truth event
    tp_precision = sum(1 for p in valid_pred if any(_events_overlap(p, t) for t in valid_true))
    precision = tp_precision / len(valid_pred) if valid_pred else float(zero_division)

    # F1 score
    if precision + recall > 0:
        f1 = (2 * precision * recall) / (precision + recall)
    else:
        f1 = float(zero_division)

    return {
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1": round(float(f1), 4),
    }


def detection_latency(
    y_true_events: Sequence[tuple[int, int]],
    y_pred_events: Sequence[tuple[int, int]],
) -> float:
    """
    Compute mean detection latency (in time steps) across matched events.

    For each ground-truth event that is detected by one or more predicted events,
    latency is defined as max(0, earliest_pred_start - true_event_start).
    If no events are matched, returns 0.0.

    Args:
        y_true_events: Ground-truth anomaly events as (start, end) index pairs.
        y_pred_events: Predicted anomaly events as (start, end) index pairs.

    Returns:
        Mean detection delay in time steps across all matched events.

    Raises:
        ValueError: If any event interval is malformed or invalid.
    """
    valid_true = [_validate_event(ev) for ev in y_true_events]
    valid_pred = [_validate_event(ev) for ev in y_pred_events]

    latencies: list[int] = []

    for t_start, t_end in valid_true:
        overlapping_preds = [p for p in valid_pred if _events_overlap((t_start, t_end), p)]
        if overlapping_preds:
            earliest_det = min(p[0] for p in overlapping_preds)
            delay = max(0, earliest_det - t_start)
            latencies.append(delay)

    if not latencies:
        return 0.0

    return round(float(sum(latencies) / len(latencies)), 4)


def subsystem_attribution_accuracy(
    y_true_subsystems: Sequence[str],
    y_pred_subsystems: Sequence[str],
) -> float:
    """
    Compute fraction of correctly attributed subsystems.

    Names are normalized case-insensitively and stripped of enum prefixes.

    Args:
        y_true_subsystems: Ground-truth attributed subsystem names.
        y_pred_subsystems: Predicted attributed subsystem names.

    Returns:
        Attribution accuracy in [0.0, 1.0].

    Raises:
        ValueError: If sequences have unequal lengths.
    """
    if len(y_true_subsystems) != len(y_pred_subsystems):
        raise ValueError(
            f"Length mismatch: y_true_subsystems ({len(y_true_subsystems)}) vs "
            f"y_pred_subsystems ({len(y_pred_subsystems)})."
        )

    if not y_true_subsystems:
        return 0.0

    def _norm(s: Any) -> str:
        val = str(s).strip().lower()
        if val.startswith("subsystem."):
            val = val.split(".", 1)[1]
        return val

    correct = sum(
        1
        for yt, yp in zip(y_true_subsystems, y_pred_subsystems, strict=True)
        if _norm(yt) == _norm(yp)
    )

    return round(float(correct / len(y_true_subsystems)), 4)


def ungrounded_statement_rate(
    total_explanations: int,
    ungrounded_count: int,
) -> float:
    """
    Compute ungrounded-statement rate = ungrounded_count / total_explanations.

    Args:
        total_explanations: Total number of generated explanation statements.
        ungrounded_count: Number of ungrounded or unverifiable claims.

    Returns:
        Rate in [0.0, 1.0]. Returns 0.0 if total_explanations == 0.

    Raises:
        ValueError: If inputs are negative or ungrounded_count > total_explanations.
    """
    if (
        not isinstance(total_explanations, int)
        or isinstance(total_explanations, bool)
        or total_explanations < 0
    ):
        raise ValueError(
            f"total_explanations must be a non-negative integer, got {total_explanations!r}"
        )
    if (
        not isinstance(ungrounded_count, int)
        or isinstance(ungrounded_count, bool)
        or ungrounded_count < 0
    ):
        raise ValueError(
            f"ungrounded_count must be a non-negative integer, got {ungrounded_count!r}"
        )
    if ungrounded_count > total_explanations:
        raise ValueError(
            f"ungrounded_count ({ungrounded_count}) cannot exceed total_explanations ({total_explanations})."
        )

    if total_explanations == 0:
        return 0.0

    return round(float(ungrounded_count / total_explanations), 4)


def point_adjusted_precision_recall_f1(
    y_true: Sequence[bool],
    y_pred: Sequence[bool],
    *,
    zero_division: float = 0.0,
) -> dict[str, float]:
    """
    Compute point-adjusted precision, recall, and F1 (ADR-0002 Rule R4 labelled comparison).

    If any time point in a contiguous ground-truth anomaly segment is detected,
    all points in that ground-truth segment are treated as detected in the adjusted prediction.

    Args:
        y_true: Ground-truth binary sequence.
        y_pred: Predicted binary sequence.
        zero_division: Return value when denominator is 0 (default 0.0).

    Returns:
        dict with keys 'precision', 'recall', 'f1' rounded to 4 decimal places.

    Raises:
        ValueError: If sequences have unequal lengths.
    """
    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: y_true ({len(y_true)}) vs y_pred ({len(y_pred)}).")

    if not y_true:
        return {
            "precision": float(zero_division),
            "recall": float(zero_division),
            "f1": float(zero_division),
        }

    # Copy predictions for adjustment
    adjusted_pred = list(y_pred)
    true_events = binary_to_events(y_true)

    for start_idx, end_idx in true_events:
        # If any point in the segment is predicted anomalous, adjust entire segment to True
        if any(y_pred[i] for i in range(start_idx, end_idx + 1)):
            for i in range(start_idx, end_idx + 1):
                adjusted_pred[i] = True

    tp = sum(1 for yt, yp in zip(y_true, adjusted_pred, strict=True) if yt and yp)
    fp = sum(1 for yt, yp in zip(y_true, adjusted_pred, strict=True) if not yt and yp)
    fn = sum(1 for yt, yp in zip(y_true, adjusted_pred, strict=True) if yt and not yp)

    precision = tp / (tp + fp) if (tp + fp) > 0 else float(zero_division)
    recall = tp / (tp + fn) if (tp + fn) > 0 else float(zero_division)
    f1 = (
        (2 * precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else float(zero_division)
    )

    return {
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1": round(float(f1), 4),
    }
