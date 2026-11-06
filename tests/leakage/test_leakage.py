"""
tests.leakage.test_leakage
============================
Leakage regression suite — Permanent CI check (Tasks T0.9 & T0.10).

Design:
  1. A fixture that constructs a window list with a DELIBERATE look-ahead
     split bug (test data contains timestamps BEFORE the train boundary).
  2. Verified test on the production split function asserting zero leakage.
  3. Regression test verifying that assert_no_future_leakage correctly raises
     if leakage is attempted.

Owner:   Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    0 (task T0.10)
Status:  complete — permanent regression suite active and passing.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from libs.common.helpers import assert_no_future_leakage, chronological_split_indices

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_timestamps(n: int, start: datetime) -> list[datetime]:
    """Generate n hourly timestamps starting from start."""
    return [start + timedelta(hours=i) for i in range(n)]


# ---------------------------------------------------------------------------
# Fixture: planted look-ahead bug
# ---------------------------------------------------------------------------


def _buggy_shuffle_split(
    timestamps: list[datetime],
    test_fraction: float = 0.2,
) -> tuple[list[datetime], list[datetime]]:
    """
    INTENTIONALLY BUGGY split that randomly shuffles before splitting.
    This simulates the classic time-series data leakage mistake.
    """
    import random

    rng = random.Random(42)  # fixed seed for reproducibility
    shuffled = list(timestamps)
    rng.shuffle(shuffled)
    split_idx = int(len(shuffled) * (1 - test_fraction))
    return shuffled[:split_idx], shuffled[split_idx:]


def _detect_leakage(
    train_timestamps: list[datetime],
    test_timestamps: list[datetime],
) -> bool:
    """
    Return True if any test timestamp precedes the latest train timestamp.
    """
    if not train_timestamps or not test_timestamps:
        return False
    max_train = max(train_timestamps)
    return any(t < max_train for t in test_timestamps)


# ---------------------------------------------------------------------------
# Test 1: planted bug IS detectable
# ---------------------------------------------------------------------------


def test_planted_leakage_bug_is_detectable() -> None:
    """Verify that our leakage detection helper catches the deliberate bug."""
    base = datetime(2024, 1, 1, tzinfo=UTC)
    timestamps = _make_timestamps(100, base)

    train_ts, test_ts = _buggy_shuffle_split(timestamps, test_fraction=0.2)
    assert _detect_leakage(train_ts, test_ts), (
        "The planted shuffle-split bug should cause test timestamps to "
        "appear before the latest train timestamp."
    )


# ---------------------------------------------------------------------------
# Test 2: production chronological_split_indices must NOT leak
# ---------------------------------------------------------------------------


def test_production_split_no_leakage() -> None:
    """
    Assert that production chronological_split_indices never places
    a test timestamp before the latest train timestamp.
    """
    base = datetime(2024, 1, 1, tzinfo=UTC)
    timestamps = _make_timestamps(100, base)

    train_idx, test_idx = chronological_split_indices(timestamps, test_fraction=0.2)
    train_ts = [timestamps[i] for i in train_idx]
    test_ts = [timestamps[i] for i in test_idx]

    # Verify zero leakage
    assert not _detect_leakage(train_ts, test_ts), (
        "DATA LEAKAGE DETECTED: test timestamps appear before the latest "
        "train timestamp. The chronological split is broken."
    )
    # Also verify assert_no_future_leakage does not raise
    assert_no_future_leakage(train_ts, test_ts)


# ---------------------------------------------------------------------------
# Test 3: assert_no_future_leakage catches simulated leakage
# ---------------------------------------------------------------------------


def test_assert_no_future_leakage_raises_on_bug() -> None:
    """Verify that assert_no_future_leakage raises AssertionError if leakage occurs."""
    t0 = datetime(2024, 1, 1, tzinfo=UTC)
    train_ts = [t0 + timedelta(hours=i) for i in range(10)]
    # Leakage: test timestamp starts before the end of train
    leaky_test_ts = [t0 + timedelta(hours=5), t0 + timedelta(hours=11)]

    with pytest.raises(AssertionError, match="DATA LEAKAGE DETECTED"):
        assert_no_future_leakage(train_ts, leaky_test_ts)
