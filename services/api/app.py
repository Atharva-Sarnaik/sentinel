"""
services.api.app
==================
FastAPI service exposing Sentinel endpoints.

Endpoints (stubbed):
  POST /analyze     — submit a telemetry window, receive FusionDecision
  GET  /runs/{id}   — retrieve a RunManifest
  GET  /audit/{id}  — retrieve an AuditEntry

Owner:   Sujal Hede (@Sujalhede)
Tier:    5 (task T5.2)
Status:  not started
"""

from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(
    title="Sentinel API",
    description=(
        "Multi-Agent AI System for Satellite Telemetry "
        "Health Monitoring and Anomaly Detection. "
        "Status: scaffolding, implementation not started."
    ),
    version="0.0.1.dev0",
)


@app.post("/analyze")
async def analyze(body: dict) -> dict:
    """Submit a TelemetryWindow for multi-agent analysis."""
    # TODO (T5.2): implement analyze endpoint.
    raise NotImplementedError("POST /analyze: implementation pending task T5.2.")


@app.get("/runs/{run_id}")
async def get_run(run_id: str) -> dict:
    """Retrieve a RunManifest by run_id."""
    # TODO (T5.2): implement run retrieval.
    raise NotImplementedError("GET /runs/{run_id}: implementation pending task T5.2.")


@app.get("/audit/{entry_id}")
async def get_audit_entry(entry_id: str) -> dict:
    """Retrieve an AuditEntry by entry_id."""
    # TODO (T5.2): implement audit entry retrieval.
    raise NotImplementedError("GET /audit/{entry_id}: implementation pending task T5.2.")
