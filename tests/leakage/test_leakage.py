"""
tests.leakage.test_leakage
============================
Leakage regression suite — Permanent CI check (task T0.10).

Design:
  1. A fixture that constructs a window list with a DELIBERATE look-ahead
     split bug (test data contains timestamps BEFORE the train boundary).
  2. A test that uses the production split function and asserts the bug
     is caught — marked xfail(strict=True) until T0.9/T0.10 are implemented.
  3. A test that verifies the planted bug in the fixture is detectable —
     this test must PASS immediately (it only tests the fixture itself).

Owner:   Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    0 (task T0.10)
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

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

    The leakage regression suite must detect that test timestamps
    appear before the latest train timestamp.
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
    This is the leakage condition we want the production suite to catch.
    """
    if not train_timestamps or not test_timestamps:
        return False
    max_train = max(train_timestamps)
    return any(t < max_train for t in test_timestamps)


# ---------------------------------------------------------------------------
# Test 1: planted bug IS detectable (must pass now — no xfail)
# ---------------------------------------------------------------------------


def test_planted_leakage_bug_is_detectable() -> None:
    """
    Verify that our leakage detection helper catches the deliberate
    shuffle-split bug in _buggy_shuffle_split.

    This test validates the TEST INFRASTRUCTURE, not production code.
    It must pass on a fresh clone (no production implementation needed).
    """
    base = datetime(2024, 1, 1, tzinfo=UTC)
    timestamps = _make_timestamps(100, base)

    train_ts, test_ts = _buggy_shuffle_split(timestamps, test_fraction=0.2)
    assert _detect_leakage(train_ts, test_ts), (
        "The planted shuffle-split bug should cause test timestamps to "
        "appear before the latest train timestamp — but it didn't. "
        "Check _buggy_shuffle_split implementation."
    )


# ---------------------------------------------------------------------------
# Test 2: production chronological_split_indices must NOT leak
#         (xfail strict until T0.9 / T0.10 are implemented)
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    strict=True,
    reason=(
        "chronological_split_indices not yet implemented (task T0.9). "
        "This test must fail until the production split function exists "
        "and is verified leakage-free."
    ),
)
def test_production_split_no_leakage() -> None:
    """
    Assert that the production chronological_split_indices never places
    a test timestamp before the latest train timestamp.

    Marked xfail(strict=True): must fail until T0.9 is implemented.
    Once implemented, remove the xfail marker — the test must then pass.
    """
    from libs.common.helpers import chronological_split_indices

    base = datetime(2024, 1, 1, tzinfo=UTC)
    timestamps = _make_timestamps(100, base)

    train_idx, test_idx = chronological_split_indices(timestamps, test_fraction=0.2)
    train_ts = [timestamps[i] for i in train_idx]
    test_ts = [timestamps[i] for i in test_idx]

    assert not _detect_leakage(train_ts, test_ts), (
        "DATA LEAKAGE DETECTED: test timestamps appear before the latest "
        "train timestamp. The chronological split is broken."
    )
