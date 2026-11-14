"""
services.evaluation.golden_set.loader
=======================================
Loader and data model for the T4.3 explanation grounding golden dataset.

Owner:   Sujal Hede (@Sujalhede)
Tier:    4 (task T4.3)
Status:  complete — golden dataset model and loader.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from libs.contracts import Explanation, FusionDecision, VerifierResult, VerifierStatus

DEFAULT_DATASET_PATH = Path(__file__).resolve().parent / "grounding_golden_set.json"
FALLBACK_FIXTURE_PATH = (
    Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "grounding_golden_set.json"
)

VALID_CATEGORIES = {
    "fully_grounded",
    "unsupported_numerical_claim",
    "invented_telemetry_observation",
    "incorrect_subsystem_attribution",
    "unsupported_anomaly_severity",
    "contradiction_with_evidence",
    "missing_causal_evidence",
    "partially_grounded",
}

VALID_LABELS = {"grounded", "ungrounded"}


@dataclass(frozen=True)
class GroundingGoldenExample:
    """
    Validated golden example for explanation grounding evaluation.

    Attributes:
        id: Unique identifier for the example.
        category: Grounding category (e.g. fully_grounded, unsupported_numerical_claim).
        ground_truth_label: Ground-truth label string ('grounded' or 'ungrounded').
        is_grounded: Boolean representation of the ground-truth label.
        reason: Explanation justifying the ground-truth label.
        evidence: Fused multi-agent anomaly decision serving as ground-truth context.
        explanation: LLM-generated explanation to evaluate.
        expected_verifier_result: Expected VerifierResult output from verifier.
    """

    id: str
    category: str
    ground_truth_label: str
    is_grounded: bool
    reason: str
    evidence: FusionDecision
    explanation: Explanation
    expected_verifier_result: VerifierResult

    def __post_init__(self) -> None:
        """Validate integrity constraints on the golden example."""
        if not self.id:
            raise ValueError("Golden example ID cannot be empty.")
        if self.category not in VALID_CATEGORIES:
            raise ValueError(
                f"Invalid category '{self.category}'. Expected one of {sorted(VALID_CATEGORIES)}"
            )
        if self.ground_truth_label not in VALID_LABELS:
            raise ValueError(
                f"Invalid ground_truth_label '{self.ground_truth_label}'. Expected one of {sorted(VALID_LABELS)}"
            )
        expected_bool = self.ground_truth_label == "grounded"
        if self.is_grounded != expected_bool:
            raise ValueError(
                f"is_grounded ({self.is_grounded}) does not match ground_truth_label '{self.ground_truth_label}'."
            )
        expected_status = VerifierStatus.GROUNDED if self.is_grounded else VerifierStatus.UNGROUNDED
        if self.expected_verifier_result.status != expected_status:
            raise ValueError(
                f"expected_verifier_result status '{self.expected_verifier_result.status}' "
                f"mismatches ground_truth_label '{self.ground_truth_label}'."
            )
        if str(self.evidence.decision_id) != str(self.explanation.decision_id):
            raise ValueError(
                f"decision_id mismatch: evidence ({self.evidence.decision_id}) vs "
                f"explanation ({self.explanation.decision_id})"
            )
        if str(self.explanation.explanation_id) != str(
            self.expected_verifier_result.explanation_id
        ):
            raise ValueError(
                f"explanation_id mismatch: explanation ({self.explanation.explanation_id}) vs "
                f"expected_verifier_result ({self.expected_verifier_result.explanation_id})"
            )


def resolve_golden_set_path(path: Path | str | None = None) -> Path:
    """Resolve the filesystem path to the golden dataset JSON file."""
    if path is not None:
        p = Path(path)
        if p.is_file():
            return p
        raise FileNotFoundError(f"Golden dataset file not found at: {path}")

    if DEFAULT_DATASET_PATH.is_file():
        return DEFAULT_DATASET_PATH
    if FALLBACK_FIXTURE_PATH.is_file():
        return FALLBACK_FIXTURE_PATH

    raise FileNotFoundError(
        f"Golden dataset file not found. Checked default '{DEFAULT_DATASET_PATH}' "
        f"and fallback '{FALLBACK_FIXTURE_PATH}'."
    )


def load_raw_golden_set(path: Path | str | None = None) -> list[dict[str, Any]]:
    """
    Load raw JSON records from the golden dataset.

    Args:
        path: Optional explicit file path.

    Returns:
        List of raw dictionaries parsed from JSON.
    """
    target_path = resolve_golden_set_path(path)
    try:
        with open(target_path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Malformed golden dataset at {target_path}: {exc}") from exc

    if not isinstance(data, list):
        raise ValueError(
            f"Malformed golden dataset at {target_path}: top-level must be a list of records."
        )
    return data


def load_grounding_golden_set(path: Path | str | None = None) -> list[GroundingGoldenExample]:
    """
    Load and validate the explanation grounding golden dataset into typed contract objects.

    Args:
        path: Optional explicit file path.

    Returns:
        List of GroundingGoldenExample objects.

    Raises:
        FileNotFoundError: If the dataset file does not exist.
        ValueError: If JSON is malformed or records fail contract validation.
    """
    raw_records = load_raw_golden_set(path)
    seen_ids: set[str] = set()
    examples: list[GroundingGoldenExample] = []

    for idx, record in enumerate(raw_records):
        if not isinstance(record, dict):
            raise ValueError(f"Record at index {idx} is not a dictionary.")

        rec_id = record.get("id")
        if not rec_id or not isinstance(rec_id, str):
            raise ValueError(f"Record at index {idx} has missing or non-string 'id'.")
        if rec_id in seen_ids:
            raise ValueError(f"Duplicate example ID '{rec_id}' encountered at index {idx}.")
        seen_ids.add(rec_id)

        try:
            evidence = FusionDecision.model_validate(record["evidence"])
            explanation = Explanation.model_validate(record["explanation"])
            expected_res = VerifierResult.model_validate(record["expected_verifier_result"])

            ex = GroundingGoldenExample(
                id=rec_id,
                category=str(record["category"]),
                ground_truth_label=str(record["ground_truth_label"]),
                is_grounded=bool(record["is_grounded"]),
                reason=str(record["reason"]),
                evidence=evidence,
                explanation=explanation,
                expected_verifier_result=expected_res,
            )
            examples.append(ex)
        except Exception as exc:
            raise ValueError(f"Failed to validate golden example '{rec_id}': {exc}") from exc

    return examples
