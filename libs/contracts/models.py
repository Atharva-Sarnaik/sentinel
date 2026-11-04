"""
libs.contracts.models
=====================
Frozen Pydantic v2 data contracts shared across all services.

IMPORTANT – design rules (ADR-0002):
  • The LLM never decides severity or alert level.
    FusionDecision.severity is set by the deterministic fusion engine.
  • Explanation carries evidence references only; the verifier rejects
    any claim citing a channel, value or severity absent from the evidence.
  • All models are frozen (immutable after construction).

Status: scaffolding — field definitions are illustrative stubs.
        No business logic is implemented.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class Subsystem(StrEnum):
    """The four specialist subsystems."""

    POWER = "power"
    THERMAL = "thermal"
    ATTITUDE = "attitude"
    COMMUNICATIONS = "communications"


class Severity(StrEnum):
    """Anomaly severity levels — set by fusion engine only, never by LLM."""

    NOMINAL = "nominal"
    ADVISORY = "advisory"
    WARNING = "warning"
    CRITICAL = "critical"


class VerifierStatus(StrEnum):
    """Outcome of the verifier grounding check."""

    GROUNDED = "grounded"
    UNGROUNDED = "ungrounded"
    ABSTAINED = "abstained"


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------


class _FrozenModel(BaseModel):
    """Shared base: all contracts are frozen and forbid extra fields."""

    model_config = ConfigDict(frozen=True, extra="forbid")


# ---------------------------------------------------------------------------
# TelemetryWindow
# ---------------------------------------------------------------------------


class TelemetryWindow(BaseModel):
    """
    A fixed-length slice of raw telemetry, strictly chronological.

    Design rule: windows must never overlap train/test boundaries.
    The chronological split is enforced by services.feature_plane.splits.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    window_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    subsystem: Subsystem
    start_time: datetime
    end_time: datetime
    # channel_name -> list[float] (time-ordered, length = window_size)
    channels: dict[str, list[float]] = Field(default_factory=dict)
    source_dataset: str = Field(description="Dataset identifier, e.g. 'SMAP', 'MSL', 'ESA-ADB'.")
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# SpecialistOpinion
# ---------------------------------------------------------------------------


class SpecialistOpinion(BaseModel):
    """
    Output of one specialist agent after analysing a TelemetryWindow.

    anomaly_score is a float in [0, 1] produced by the LSTM-AE
    reconstruction error after nonparametric dynamic thresholding.
    severity is a preliminary label; the fusion engine may override it.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    opinion_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    window_id: uuid.UUID
    subsystem: Subsystem
    anomaly_score: float = Field(ge=0.0, le=1.0)
    severity: Severity
    responsible_channels: list[str] = Field(default_factory=list)
    threshold_used: float
    model_run_id: str = Field(description="MLflow run ID for the specialist model used.")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ---------------------------------------------------------------------------
# FusionDecision
# ---------------------------------------------------------------------------


class FusionDecision(BaseModel):
    """
    Output of the deterministic fusion engine.

    Design rule (ADR-0002): severity and alert_level are set HERE,
    not by the LLM. The LLM receives this object as read-only evidence.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    decision_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    window_id: uuid.UUID
    opinions: list[SpecialistOpinion]
    severity: Severity
    # Which subsystems corroborate the anomaly
    corroborating_subsystems: list[Subsystem] = Field(default_factory=list)
    attributed_subsystem: Subsystem | None = None
    fusion_rule_applied: str = Field(
        description="Human-readable label of the corroboration rule that fired."
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ---------------------------------------------------------------------------
# Explanation
# ---------------------------------------------------------------------------


class Explanation(BaseModel):
    """
    Natural-language explanation produced by the LLM reasoner.

    The explanation must cite only channels, values and severity present
    in the evidence object (FusionDecision). The verifier enforces this.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    explanation_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    decision_id: uuid.UUID
    text: str = Field(description="Natural-language explanation from the LLM.")
    # Structured citations that the verifier checks against FusionDecision
    cited_channels: list[str] = Field(default_factory=list)
    cited_severity: Severity
    prompt_version: str = Field(description="Git tag or hash of the prompt template used.")
    llm_model: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ---------------------------------------------------------------------------
# VerifierResult
# ---------------------------------------------------------------------------


class VerifierResult(BaseModel):
    """
    Output of the grounding verifier.

    If status is UNGROUNDED after max retries, the system abstains and
    emits an evidence-only report (see ADR-0002, retry policy).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    verifier_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    explanation_id: uuid.UUID
    status: VerifierStatus
    # Channels or values cited in explanation but absent from evidence
    ungrounded_claims: list[str] = Field(default_factory=list)
    retry_count: int = Field(ge=0, le=2)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ---------------------------------------------------------------------------
# AuditEntry
# ---------------------------------------------------------------------------


class AuditEntry(BaseModel):
    """
    Immutable audit log record written before any downstream outcome is joined.

    Design rule: AuditEntry is written atomically before the system acts
    on a decision. It must never be modified after creation.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    entry_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    run_id: str
    window_id: uuid.UUID
    decision_id: uuid.UUID
    verifier_id: uuid.UUID
    final_severity: Severity
    abstained: bool
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    extra: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# RunManifest
# ---------------------------------------------------------------------------


class RunManifest(BaseModel):
    """
    Metadata for a full evaluation or inference run.

    Ties together MLflow run IDs, DVC dataset hashes and config hashes
    so that any reported result can be traced back to exact inputs.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    dataset_dvc_hash: str
    config_hash: str
    mlflow_experiment_id: str
    mlflow_run_ids: dict[str, str] = Field(description="subsystem_name -> mlflow run ID")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    git_commit: str | None = None
    artifact_dir: Path | None = None
