"""
services.api.app
==================
FastAPI web service exposing Sentinel endpoints for telemetry analysis and run retrieval (Task T5.2).

Endpoints:
  POST /analyze         — submit a TelemetryWindow for multi-agent health analysis
  GET  /runs            — list all stored RunManifests
  GET  /runs/{run_id}   — retrieve a specific RunManifest and its metrics
  GET  /audit/{entry_id}— retrieve an immutable AuditEntry by ID
  GET  /health          — service health check

Design Rules (ADR-0002):
  • LLM never decides severity; fusion engine decides.
  • Dynamic dispatch used for inter-service coordination to obey import-linter contracts.

Owner:   Sujal Hede (@Sujalhede)
Tier:    5 (task T5.2)
Status:  complete — typed FastAPI endpoints with validation and error handling.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from libs.common.manifest import ManifestStore
from libs.contracts import TelemetryWindow

app = FastAPI(
    title="Sentinel Telemetry Health & Anomaly Detection API",
    description=(
        "Decision-support research prototype providing multi-agent health monitoring, "
        "deterministic severity fusion, grounded LLM explanations, and immutable audit logging."
    ),
    version="0.1.0",
)

# Minimum safe CORS configuration for local Next.js frontend origin (Task Phase 2)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_manifest_store() -> ManifestStore:
    """Retrieve the active ManifestStore instance."""
    return ManifestStore()


def _serialize_outcome(outcome: dict[str, Any]) -> dict[str, Any]:
    """Helper to convert Pydantic objects, UUIDs, and datetimes in pipeline outcome to JSON-safe dict."""
    res: dict[str, Any] = {}
    for k, v in outcome.items():
        if hasattr(v, "model_dump"):
            res[k] = v.model_dump(mode="json")
        elif isinstance(v, UUID):
            res[k] = str(v)
        elif isinstance(v, (str, int, float, bool)) or v is None:
            res[k] = v
        elif isinstance(v, list):
            res[k] = [
                item.model_dump(mode="json") if hasattr(item, "model_dump") else item for item in v
            ]
        else:
            res[k] = str(v)
    return res


@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    """Service health check endpoint."""
    return {
        "status": "healthy",
        "service": "Sentinel API",
        "version": "0.1.0",
        "tier": "5",
    }


@app.post(
    "/analyze",
    status_code=status.HTTP_200_OK,
    tags=["Analysis"],
    summary="Analyze telemetry window through multi-agent pipeline",
)
async def analyze_telemetry_window(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """
    Submit a TelemetryWindow payload for end-to-end multi-agent health analysis.

    Executes:
      1. Validation of TelemetryWindow contract.
      2. Specialist opinion generation.
      3. Deterministic fusion severity scoring.
      4. Grounded LLM reasoner explanation.
      5. Verifier grounding check (max 2 retries, then abstain).
      6. Immutable audit log write before outcome is returned.
    """
    try:
        window = TelemetryWindow.model_validate(payload)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid TelemetryWindow schema: {e}",
        ) from e

    try:
        # Dynamically dispatch to orchestrator to adhere to import-linter independence rule
        orch_module = importlib.import_module("services.orchestrator.graph")
        run_fn = orch_module.run_pipeline
        outcome = run_fn(window.model_dump())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline execution error: {e}",
        ) from e

    return _serialize_outcome(outcome)


@app.get("/runs", tags=["Experiments"])
async def list_runs() -> list[dict[str, Any]]:
    """List all saved experimental run manifests."""
    store = get_manifest_store()
    manifests = store.list_all()
    return [m.model_dump(mode="json") for m in manifests]


@app.get("/runs/{run_id}", tags=["Experiments"])
async def get_run_manifest(run_id: str) -> dict[str, Any]:
    """Retrieve RunManifest and metrics.json for a specific experiment run ID."""
    store = get_manifest_store()
    manifest = store.get(run_id)
    if not manifest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found in manifest store.",
        )

    metrics_path = Path("artifacts/runs") / run_id / "metrics.json"
    metrics_data = {}
    if metrics_path.is_file():
        try:
            metrics_data = json.loads(metrics_path.read_text(encoding="utf-8"))
        except Exception:
            metrics_data = {"error": "Could not parse metrics.json"}

    return {
        "manifest": manifest.model_dump(mode="json"),
        "metrics": metrics_data,
    }


@app.get("/audit/{entry_id}", tags=["Audit"])
async def get_audit(entry_id: str) -> dict[str, Any]:
    """Retrieve an immutable AuditEntry by its unique entry ID."""
    try:
        entry_uuid = UUID(entry_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid UUID format: '{entry_id}'.",
        ) from e

    try:
        # Dynamically dispatch to audit service
        audit_module = importlib.import_module("services.audit.log_writer")
        get_fn = audit_module.get_audit_entry
        entry = get_fn(entry_uuid)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audit log query error: {e}",
        ) from e

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit entry '{entry_id}' not found.",
        )

    return entry.model_dump(mode="json")


# ---------------------------------------------------------------------------
# Historical Telemetry Replay Endpoints (Phase 3)
# ---------------------------------------------------------------------------


class ReplayStartPayload(BaseModel):
    """Payload schema for starting a NASA SMAP/MSL historical telemetry replay session."""

    dataset: str = Field(default="SMAP", description="Dataset identifier: SMAP or MSL")
    split: str = Field(default="test", description="Dataset split: train or test")
    channel: str = Field(default="P-1", description="Canonical channel ID, e.g. P-1")
    window_size: int = Field(default=100, ge=10, description="Window size in time steps")
    stride: int = Field(default=10, ge=1, description="Stride size in time steps")
    speed_delay_ms: int = Field(default=500, ge=0, description="Interval in ms between windows (0 = full speed)")
    max_windows: int | None = Field(default=None, description="Optional upper bound on windows for testing")


@app.get("/replay/channels", tags=["Historical Replay"])
async def list_replay_channels() -> dict[str, Any]:
    """Retrieve full catalog of available NASA SMAP/MSL datasets, splits, and annotated channels."""
    try:
        replay_module = importlib.import_module("services.data_plane.replay")
        return replay_module.get_replay_catalog()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load replay channels catalog: {e}",
        ) from e


@app.get("/replay/status", tags=["Historical Replay"])
async def get_replay_status() -> dict[str, Any]:
    """Retrieve current historical replay session state, progress, and latest analysis results."""
    try:
        replay_module = importlib.import_module("services.data_plane.replay")
        manager = replay_module.replay_manager
        return manager.get_status()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query replay status: {e}",
        ) from e


@app.post("/replay/start", tags=["Historical Replay"])
async def start_replay(payload: ReplayStartPayload) -> dict[str, Any]:
    """Initialize and start a historical telemetry replay session."""
    try:
        replay_module = importlib.import_module("services.data_plane.replay")
        manager = replay_module.replay_manager
        status_dict = await manager.start(
            dataset=payload.dataset,
            split=payload.split,
            channel=payload.channel,
            window_size=payload.window_size,
            stride=payload.stride,
            speed_delay_ms=payload.speed_delay_ms,
            max_windows=payload.max_windows,
        )
        return status_dict
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start replay session: {e}",
        ) from e


@app.post("/replay/pause", tags=["Historical Replay"])
async def pause_replay() -> dict[str, Any]:
    """Pause the actively running replay session."""
    try:
        replay_module = importlib.import_module("services.data_plane.replay")
        manager = replay_module.replay_manager
        return await manager.pause()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause replay session: {e}",
        ) from e


@app.post("/replay/resume", tags=["Historical Replay"])
async def resume_replay() -> dict[str, Any]:
    """Resume a paused replay session."""
    try:
        replay_module = importlib.import_module("services.data_plane.replay")
        manager = replay_module.replay_manager
        return await manager.resume()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume replay session: {e}",
        ) from e


@app.post("/replay/stop", tags=["Historical Replay"])
async def stop_replay() -> dict[str, Any]:
    """Stop and terminate the active replay session."""
    try:
        replay_module = importlib.import_module("services.data_plane.replay")
        manager = replay_module.replay_manager
        return await manager.stop()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop replay session: {e}",
        ) from e

