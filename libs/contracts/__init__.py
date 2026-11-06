"""
libs.contracts
==============
Frozen Pydantic v2 models shared by all services.

Design rule (ADR-0002): These models are the **only** permitted
cross-service data contracts. Services must not share mutable state
or import each other's internals.

Status: Tier 0 complete — frozen contracts with validation.
"""

from libs.contracts.models import (
    AuditEntry,
    Explanation,
    FusionDecision,
    RunManifest,
    Severity,
    SpecialistOpinion,
    Subsystem,
    TelemetryWindow,
    VerifierResult,
    VerifierStatus,
)

__all__ = [
    "Subsystem",
    "Severity",
    "VerifierStatus",
    "TelemetryWindow",
    "SpecialistOpinion",
    "FusionDecision",
    "Explanation",
    "VerifierResult",
    "AuditEntry",
    "RunManifest",
]
