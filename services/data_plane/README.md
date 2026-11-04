# data_plane

**Purpose:** Ingest raw satellite telemetry and deliver validated, chronological `TelemetryWindow` objects to the feature plane.

**Inputs:** Raw telemetry files in `data/raw/` (DVC-tracked, gitignored).

**Outputs:** `libs.contracts.TelemetryWindow` (one per subsystem per window).

**Key modules:**
| Module | Description |
|---|---|
| `adapter.py` | NASA SMAP/MSL replay adapter; fallback: ESA-ADB, OPS-SAT |
| `integrity_gate.py` | Schema, range, and staleness validation |

**Owner:** Sujal Hede (`@Sujalhede`) — adapter, replay; Atharva Sarnaik (`@Atharva-Sarnaik`) — integrity gate

**Tier:** 0 | **Tasks:** T0.7, T0.8

**Status:** `not started`

> **Risk R1:** The SMAP/MSL channel-to-subsystem grouping is unverified. Task T0.5 is a feasibility spike. ADR-0001 records the final dataset decision.

