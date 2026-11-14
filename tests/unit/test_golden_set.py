"""
tests.unit.test_golden_set
==========================
Unit tests for the T4.3 explanation grounding golden dataset and loader.

Owner:   Sujal Hede (@Sujalhede)
Tier:    4 (task T4.3)
Status:  complete — tests dataset loading, uniqueness, schema compliance,
         positive/negative coverage, determinism, and verifier integration.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from libs.contracts import (
    Explanation,
    FusionDecision,
    Subsystem,
    VerifierResult,
    VerifierStatus,
)
from services.evaluation.golden_set import (
    DEFAULT_DATASET_PATH,
    FALLBACK_FIXTURE_PATH,
    VALID_CATEGORIES,
    VALID_LABELS,
    GroundingGoldenExample,
    load_grounding_golden_set,
    load_raw_golden_set,
)
from services.verifier.grounding import check_grounding


def test_golden_set_files_exist() -> None:
    """Verify that both canonical and fallback golden dataset files exist and are non-empty."""
    assert DEFAULT_DATASET_PATH.is_file(), f"Missing default file: {DEFAULT_DATASET_PATH}"
    assert FALLBACK_FIXTURE_PATH.is_file(), f"Missing fallback file: {FALLBACK_FIXTURE_PATH}"
    assert DEFAULT_DATASET_PATH.stat().st_size > 0
    assert FALLBACK_FIXTURE_PATH.stat().st_size > 0


def test_golden_set_loads_successfully() -> None:
    """Verify that load_grounding_golden_set parses and validates all records."""
    examples = load_grounding_golden_set()
    assert len(examples) == 18
    assert all(isinstance(ex, GroundingGoldenExample) for ex in examples)


def test_golden_set_unique_ids() -> None:
    """Verify every example has a unique ID with the standard naming convention."""
    examples = load_grounding_golden_set()
    ids = [ex.id for ex in examples]
    assert len(ids) == len(set(ids)), "Duplicate example IDs found in golden set"
    for ex_id in ids:
        assert ex_id.startswith("GOLDEN-GROUNDING-"), f"Unexpected ID prefix in '{ex_id}'"


def test_golden_set_required_fields_present() -> None:
    """Verify raw JSON objects contain all mandatory fields."""
    raw_records = load_raw_golden_set()
    required_keys = {
        "id",
        "category",
        "ground_truth_label",
        "is_grounded",
        "reason",
        "evidence",
        "explanation",
        "expected_verifier_result",
    }
    for record in raw_records:
        assert required_keys.issubset(record.keys()), (
            f"Record {record.get('id')} missing keys: {required_keys - record.keys()}"
        )


def test_golden_set_valid_labels_and_categories() -> None:
    """Verify categories and ground-truth labels belong to the defined allowed sets."""
    examples = load_grounding_golden_set()
    for ex in examples:
        assert ex.category in VALID_CATEGORIES, (
            f"Example {ex.id} has invalid category '{ex.category}'"
        )
        assert ex.ground_truth_label in VALID_LABELS, (
            f"Example {ex.id} has invalid label '{ex.ground_truth_label}'"
        )
        assert ex.is_grounded == (ex.ground_truth_label == "grounded")


def test_golden_set_contract_conformance() -> None:
    """Verify evidence, explanation, and expected verifier result match frozen Pydantic contracts."""
    examples = load_grounding_golden_set()
    for ex in examples:
        assert isinstance(ex.evidence, FusionDecision)
        assert isinstance(ex.explanation, Explanation)
        assert isinstance(ex.expected_verifier_result, VerifierResult)
        assert ex.evidence.decision_id == ex.explanation.decision_id
        assert ex.explanation.explanation_id == ex.expected_verifier_result.explanation_id


def test_golden_set_positive_examples_grounded() -> None:
    """Verify positive examples are fully grounded with zero ungrounded claims."""
    examples = load_grounding_golden_set()
    positive = [ex for ex in examples if ex.is_grounded]
    assert len(positive) == 4, f"Expected 4 positive examples, got {len(positive)}"

    for ex in positive:
        assert ex.category == "fully_grounded"
        assert ex.expected_verifier_result.status == VerifierStatus.GROUNDED
        assert ex.expected_verifier_result.is_grounded is True
        assert len(ex.expected_verifier_result.ungrounded_claims) == 0


def test_golden_set_negative_examples_coverage() -> None:
    """Verify negative examples cover all 7 failure categories with ungrounded claims."""
    examples = load_grounding_golden_set()
    negative = [ex for ex in examples if not ex.is_grounded]
    assert len(negative) == 14, f"Expected 14 negative examples, got {len(negative)}"

    negative_categories = {ex.category for ex in negative}
    expected_failure_categories = {
        "unsupported_numerical_claim",
        "invented_telemetry_observation",
        "incorrect_subsystem_attribution",
        "unsupported_anomaly_severity",
        "contradiction_with_evidence",
        "missing_causal_evidence",
        "partially_grounded",
    }
    assert negative_categories == expected_failure_categories

    for ex in negative:
        assert ex.expected_verifier_result.status == VerifierStatus.UNGROUNDED
        assert ex.expected_verifier_result.is_grounded is False
        assert len(ex.expected_verifier_result.ungrounded_claims) >= 1


def test_golden_set_subsystem_coverage() -> None:
    """Verify the golden dataset covers Power, Thermal, Attitude, Communications, and Nominal."""
    examples = load_grounding_golden_set()
    subsystems_represented: set[Subsystem | None] = set()

    for ex in examples:
        subsystems_represented.add(ex.evidence.attributed_subsystem)
        for op in ex.evidence.opinions:
            subsystems_represented.add(op.subsystem)

    assert Subsystem.POWER in subsystems_represented
    assert Subsystem.THERMAL in subsystems_represented
    assert Subsystem.ATTITUDE in subsystems_represented
    assert Subsystem.COMMUNICATIONS in subsystems_represented
    assert None in subsystems_represented  # Nominal case has attributed_subsystem=None


def test_golden_set_determinism() -> None:
    """Verify dataset loading is deterministic and produces identical objects on multiple loads."""
    run1 = load_grounding_golden_set()
    run2 = load_grounding_golden_set()

    assert len(run1) == len(run2)
    for e1, e2 in zip(run1, run2, strict=True):
        assert e1.id == e2.id
        assert e1.category == e2.category
        assert e1.ground_truth_label == e2.ground_truth_label
        assert e1.is_grounded == e2.is_grounded
        assert e1.evidence.decision_id == e2.evidence.decision_id
        assert e1.explanation.text == e2.explanation.text
        assert e1.expected_verifier_result.status == e2.expected_verifier_result.status


def test_golden_set_existing_verifier_behavior_unchanged() -> None:
    """
    Verify existing verifier behavior is preserved without modification.

    Under Tier 3 scaffolding, check_grounding raises NotImplementedError.
    This test verifies that calling check_grounding on golden examples explicitly
    reflects the repository's current status and confirms the verifier was not
    tampered with or silently mocked.
    """
    examples = load_grounding_golden_set()
    first_example = examples[0]

    with pytest.raises(NotImplementedError, match="check_grounding: implementation pending"):
        check_grounding(first_example.explanation, first_example.evidence)


def test_golden_set_loader_error_handling() -> None:
    """Verify the loader raises informative exceptions on missing or corrupted files."""
    with pytest.raises(FileNotFoundError):
        load_grounding_golden_set("non_existent_golden_set.json")

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
        tf.write("{ not a list }")
        bad_json_path = Path(tf.name)

    try:
        with pytest.raises(ValueError, match="Malformed golden dataset"):
            load_grounding_golden_set(bad_json_path)
    finally:
        bad_json_path.unlink(missing_ok=True)

    valid_record = load_raw_golden_set()[0]
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
        json.dump([valid_record, valid_record], tf)
        dup_id_path = Path(tf.name)

    try:
        with pytest.raises(ValueError, match="Duplicate example ID"):
            load_grounding_golden_set(dup_id_path)
    finally:
        dup_id_path.unlink(missing_ok=True)
