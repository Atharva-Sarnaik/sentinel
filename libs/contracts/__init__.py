"""
libs.contracts
==============
Frozen Pydantic v2 models shared by all services.

Design rule (ADR-0002): These models are the **only** permitted
cross-service data contracts. Services must not share mutable state
or import each other's internals.

Status: scaffolding — stubs only, implementation not started.
"""

from libs.contracts.models import (
    AuditEntry,
    Explanation,
    FusionDecision,
    RunManifest,
    SpecialistOpinion,
    TelemetryWindow,
    VerifierResult,
)

__all__ = [
    "TelemetryWindow",
    "SpecialistOpinion",
    "FusionDecision",
    "Explanation",
    "VerifierResult",
    "AuditEntry",
    "RunManifest",
]
