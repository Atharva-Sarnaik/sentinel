"""
tests.unit.test_metrics
=======================
Unit tests for Task T4.1: Evaluation Metrics (services.evaluation.metrics).

Covers:
  - Event-wise Precision, Recall, and F1 calculation.
  - Event overlap boundary conditions (exact, partial, disjoint, nested, single-step).
  - Detection latency (delay calculation, earliest prediction, negative prevention, unconfirmed events).
  - Subsystem attribution accuracy (case-insensitivity, enum normalization, length validation).
  - Ungrounded-statement rate (rate calculation, boundary constraints, zero division).
  - Point-adjusted scores as a labelled comparison per ADR-0002 (Rule R4).
  - Sequence-to-events and events-to-sequence bidirectional converters.

Owner:   Atharva Sarnaik (@Atharva-Sarnaik) / Sujal Hede (@Sujalhede)
Tier:    4 (task T4.1)
"""

from __future__ import annotations

import pytest

from services.evaluation.metrics import (
    binary_to_events,
    detection_latency,
    event_wise_precision_recall_f1,
    events_to_binary,
    point_adjusted_precision_recall_f1,
    subsystem_attribution_accuracy,
    ungrounded_statement_rate,
)

# ---------------------------------------------------------------------------
# 1. Event Validation & Conversions
# ---------------------------------------------------------------------------


def test_event_validation_invalid_shapes() -> None:
    """Verify that malformed event intervals raise ValueError."""
    with pytest.raises(ValueError, match="must be a 2-tuple"):
        event_wise_precision_recall_f1([(1,)], [(1, 2)])  # type: ignore[list-item]

    with pytest.raises(ValueError, match="must be a 2-tuple"):
        event_wise_precision_recall_f1([(1, 2, 3)], [(1, 2)])  # type: ignore[list-item]

    with pytest.raises(ValueError, match="Event start must be an integer"):
        event_wise_precision_recall_f1([("1", 2)], [(1, 2)])  # type: ignore[list-item]

    with pytest.raises(ValueError, match="Event start must be an integer"):
        event_wise_precision_recall_f1([(True, 2)], [(1, 2)])  # type: ignore[list-item]

    with pytest.raises(ValueError, match="Event end must be an integer"):
        event_wise_precision_recall_f1([(1, 2.5)], [(1, 2)])  # type: ignore[list-item]

    with pytest.raises(ValueError, match="must be non-negative"):
        event_wise_precision_recall_f1([(-1, 5)], [(1, 2)])

    with pytest.raises(ValueError, match="cannot exceed end"):
        event_wise_precision_recall_f1([(10, 5)], [(1, 2)])


def test_binary_to_events_and_roundtrip() -> None:
    """Verify conversion from binary sequences to events and round-trip fidelity."""
    seq = [False, True, True, False, False, True, False, True, True, True]
    events = binary_to_events(seq)
    assert events == [(1, 2), (5, 5), (7, 9)]

    reconstructed = events_to_binary(events, length=len(seq))
    assert reconstructed == seq


def test_events_to_binary_bounds() -> None:
    """Verify that events exceeding length raise ValueError."""
    with pytest.raises(ValueError, match="exceeds sequence length"):
        events_to_binary([(5, 12)], length=10)

    with pytest.raises(ValueError, match="must be non-negative"):
        events_to_binary([], length=-1)


# ---------------------------------------------------------------------------
# 2. Event-Wise Precision, Recall, and F1
# ---------------------------------------------------------------------------


def test_event_wise_metrics_perfect_match() -> None:
    """Verify that identical event intervals produce perfect precision, recall, and F1."""
    events = [(10, 20), (30, 40), (50, 60)]
    metrics = event_wise_precision_recall_f1(events, events)
    assert metrics == {"precision": 1.0, "recall": 1.0, "f1": 1.0}


def test_event_wise_metrics_partial_overlap() -> None:
    """Verify that partial interval overlaps count as successful detections."""
    y_true = [(10, 20)]
    y_pred = [(15, 25)]  # Overlaps [15, 20]
    metrics = event_wise_precision_recall_f1(y_true, y_pred)
    assert metrics == {"precision": 1.0, "recall": 1.0, "f1": 1.0}


def test_event_wise_metrics_missed_event_fn() -> None:
    """Verify recall drop when a true event is completely missed."""
    y_true = [(10, 20), (30, 40)]
    y_pred = [(10, 20)]  # Second event missed
    metrics = event_wise_precision_recall_f1(y_true, y_pred)
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 0.5
    assert metrics["f1"] == 0.6667


def test_event_wise_metrics_false_alarm_fp() -> None:
    """Verify precision drop when a predicted event does not overlap any true event."""
    y_true = [(10, 20)]
    y_pred = [(10, 20), (50, 60)]  # Second prediction is a false positive
    metrics = event_wise_precision_recall_f1(y_true, y_pred)
    assert metrics["precision"] == 0.5
    assert metrics["recall"] == 1.0
    assert metrics["f1"] == 0.6667


def test_event_wise_metrics_disjoint() -> None:
    """Verify that disjoint non-overlapping events yield 0.0 scores."""
    y_true = [(10, 20)]
    y_pred = [(21, 30)]  # Immediately adjacent but not overlapping
    metrics = event_wise_precision_recall_f1(y_true, y_pred)
    assert metrics == {"precision": 0.0, "recall": 0.0, "f1": 0.0}


def test_event_wise_metrics_multiple_preds_per_true_event() -> None:
    """Verify that multiple predicted events within a single true event count as precise hits."""
    y_true = [(10, 50)]
    y_pred = [(12, 18), (25, 30), (40, 45)]
    metrics = event_wise_precision_recall_f1(y_true, y_pred)
    assert metrics == {"precision": 1.0, "recall": 1.0, "f1": 1.0}


def test_event_wise_metrics_single_pred_spanning_multiple_true_events() -> None:
    """Verify that a single wide prediction spanning multiple true events recalls both."""
    y_true = [(10, 15), (25, 30)]
    y_pred = [(12, 28)]  # Overlaps both
    metrics = event_wise_precision_recall_f1(y_true, y_pred)
    assert metrics == {"precision": 1.0, "recall": 1.0, "f1": 1.0}


def test_event_wise_metrics_empty_inputs_and_zero_division() -> None:
    """Verify safe handling of empty input lists and customizable zero_division."""
    assert event_wise_precision_recall_f1([], []) == {
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
    }
    assert event_wise_precision_recall_f1([], [], zero_division=1.0) == {
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0,
    }
    assert event_wise_precision_recall_f1([(1, 5)], []) == {
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
    }
    assert event_wise_precision_recall_f1([], [(1, 5)]) == {
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
    }


# ---------------------------------------------------------------------------
# 3. Detection Latency
# ---------------------------------------------------------------------------


def test_detection_latency_standard_delay() -> None:
    """Verify correct computation of detection delay across matched events."""
    y_true = [(100, 150), (200, 250)]
    y_pred = [(110, 140), (220, 240)]  # Delays: 10 and 20 -> mean = 15.0
    latency = detection_latency(y_true, y_pred)
    assert latency == 15.0


def test_detection_latency_immediate_and_early() -> None:
    """Verify that simultaneous or early detections produce zero latency without negative values."""
    y_true = [(100, 150)]
    y_pred = [(90, 120)]  # Predicted before true event onset
    latency = detection_latency(y_true, y_pred)
    assert latency == 0.0


def test_detection_latency_multiple_overlapping_preds() -> None:
    """Verify that latency uses the earliest detection for each true event."""
    y_true = [(100, 150)]
    y_pred = [(120, 130), (105, 115)]  # Earliest is 105 -> delay = 5
    latency = detection_latency(y_true, y_pred)
    assert latency == 5.0


def test_detection_latency_unmatched_events() -> None:
    """Verify that unmatched events are excluded and zero matches produce 0.0."""
    y_true = [(100, 150), (300, 350)]
    y_pred = [(108, 140)]  # Only first event matched (delay 8)
    latency = detection_latency(y_true, y_pred)
    assert latency == 8.0

    # No matches at all
    assert detection_latency([(100, 150)], [(200, 250)]) == 0.0
    assert detection_latency([], []) == 0.0


# ---------------------------------------------------------------------------
# 4. Subsystem Attribution Accuracy
# ---------------------------------------------------------------------------


def test_subsystem_attribution_accuracy_basic() -> None:
    """Verify calculation of attribution accuracy."""
    y_true = ["power", "thermal", "attitude", "communications"]
    y_pred = ["power", "thermal", "power", "communications"]
    acc = subsystem_attribution_accuracy(y_true, y_pred)
    assert acc == 0.75


def test_subsystem_attribution_accuracy_normalization() -> None:
    """Verify case-insensitivity and Subsystem enum prefix handling."""
    y_true = ["Subsystem.POWER", "THERMAL", "attitude"]
    y_pred = ["power", "Subsystem.thermal", "ATTITUDE"]
    assert subsystem_attribution_accuracy(y_true, y_pred) == 1.0


def test_subsystem_attribution_accuracy_validation() -> None:
    """Verify that length mismatch raises ValueError and empty sequence returns 0.0."""
    with pytest.raises(ValueError, match="Length mismatch"):
        subsystem_attribution_accuracy(["power"], ["power", "thermal"])

    assert subsystem_attribution_accuracy([], []) == 0.0


# ---------------------------------------------------------------------------
# 5. Ungrounded-Statement Rate
# ---------------------------------------------------------------------------


def test_ungrounded_statement_rate_calculation() -> None:
    """Verify calculation of ungrounded statement rate."""
    assert ungrounded_statement_rate(10, 2) == 0.2
    assert ungrounded_statement_rate(5, 5) == 1.0
    assert ungrounded_statement_rate(5, 0) == 0.0
    assert ungrounded_statement_rate(0, 0) == 0.0


def test_ungrounded_statement_rate_validation() -> None:
    """Verify boundary checks on ungrounded-statement rate inputs."""
    with pytest.raises(ValueError, match="cannot exceed total_explanations"):
        ungrounded_statement_rate(5, 6)

    with pytest.raises(ValueError, match="must be a non-negative integer"):
        ungrounded_statement_rate(-1, 0)

    with pytest.raises(ValueError, match="must be a non-negative integer"):
        ungrounded_statement_rate(5, -1)

    with pytest.raises(ValueError, match="must be a non-negative integer"):
        ungrounded_statement_rate(True, 1)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# 6. Point-Adjusted Comparison Metric (ADR-0002 Rule R4)
# ---------------------------------------------------------------------------


def test_point_adjusted_precision_recall_f1() -> None:
    """Verify point-adjustment behavior where any hit expands to entire anomaly segment."""
    y_true = [False, True, True, True, False, False, True, True, False]
    # Prediction detects 1 point of first segment, misses second segment completely
    y_pred = [False, False, True, False, False, False, False, False, False]

    # Without PA: TP=1, FP=0, FN=4 -> Recall = 1/5 = 0.2
    # With PA: First segment [1, 3] adjusted to all True.
    # Adjusted TP=3, FP=0, FN=2 -> Recall = 3/5 = 0.6, Precision = 3/3 = 1.0
    metrics = point_adjusted_precision_recall_f1(y_true, y_pred)
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 0.6
    assert metrics["f1"] == 0.75


def test_point_adjusted_empty_and_mismatch() -> None:
    """Verify point-adjusted metric validation and zero-handling."""
    with pytest.raises(ValueError, match="Length mismatch"):
        point_adjusted_precision_recall_f1([True], [True, False])

    assert point_adjusted_precision_recall_f1([], []) == {
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
    }
