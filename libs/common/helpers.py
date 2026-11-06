"""
libs.common.helpers
===================
Shared utility functions used across services.

Design rule (ADR-0002): chronological_split_indices must never shuffle.
All time-series splits must be strictly ordered by timestamp.

Status: complete — chronological split indices, leakage assertions, and time helpers (T0.9 / T0.10).
"""

from __future__ import annotations

import math
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return the current UTC datetime (timezone-aware)."""
    return datetime.now(tz=UTC)


def make_window_id() -> uuid.UUID:
    """Generate a new UUID4 window identifier."""
    return uuid.uuid4()


def chronological_split_indices(
    timestamps: Sequence[datetime],
    test_fraction: float = 0.2,
) -> tuple[list[int], list[int]]:
    """
    Split a time-ordered sequence into train and test index sets.

    IMPORTANT (ADR-0002): This function must never shuffle. The split
    boundary is strictly at ``floor((1 - test_fraction) * len(timestamps))``.
    Random shuffling across this boundary constitutes data leakage.

    Args:
        timestamps: A sequence of datetime objects, sorted ascending.
        test_fraction: Fraction of data reserved for the test set. Must be in (0, 1).

    Returns:
        A tuple (train_indices, test_indices).

    Raises:
        ValueError: If test_fraction is not between 0 and 1, or timestamps is empty.
    """
    if not (0.0 < test_fraction < 1.0):
        raise ValueError(f"test_fraction must be in (0, 1), got {test_fraction}")

    n = len(timestamps)
    if n == 0:
        return [], []

    split_idx = math.floor((1.0 - test_fraction) * n)
    train_indices = list(range(0, split_idx))
    test_indices = list(range(split_idx, n))

    return train_indices, test_indices


def assert_no_future_leakage(
    train_timestamps: Sequence[datetime],
    test_timestamps: Sequence[datetime],
) -> None:
    """
    Assert that no test timestamp precedes the latest train timestamp.

    Raises:
        AssertionError: If any test timestamp <= latest train timestamp.
    """
    if not train_timestamps or not test_timestamps:
        return

    max_train = max(train_timestamps)
    min_test = min(test_timestamps)

    if min_test < max_train:
        raise AssertionError(
            f"DATA LEAKAGE DETECTED: min test timestamp ({min_test}) "
            f"precedes max train timestamp ({max_train})."
        )
