"""
libs.common.helpers
===================
Shared utility functions used across services.

Design rule (ADR-0002): chronological_split_indices must never shuffle.
All time-series splits must be strictly ordered by timestamp.

Status: scaffolding — stubs only, implementation not started.
"""

from __future__ import annotations

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
    boundary is always at ``floor((1 - test_fraction) * len(timestamps))``.
    Random shuffling across this boundary constitutes data leakage
    (see tests/leakage/test_leakage.py).

    Args:
        timestamps: A sequence of datetime objects, sorted ascending.
        test_fraction: Fraction of data reserved for the test set.
                       Must be in (0, 1).

    Returns:
        A tuple (train_indices, test_indices).

    Raises:
        NotImplementedError: Implementation pending task T0.9.
    """
    # TODO (T0.9): implement chronological split with boundary logging.
    raise NotImplementedError("chronological_split_indices: implementation pending task T0.9.")


def assert_no_future_leakage(
    train_timestamps: Sequence[datetime],
    test_timestamps: Sequence[datetime],
) -> None:
    """
    Assert that no test timestamp precedes the latest train timestamp.

    Used by the leakage regression suite (T0.10).

    Raises:
        NotImplementedError: Implementation pending task T0.10.
    """
    # TODO (T0.10): implement leakage assertion.
    raise NotImplementedError("assert_no_future_leakage: implementation pending task T0.10.")
