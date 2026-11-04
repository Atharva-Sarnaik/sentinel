# ADR-0001: Dataset Decision

**Status:** `draft` — pending completion of task T0.5 (feasibility spike)

**Date:** 2026-11-04

**Authors:** Atharva Sarnaik (`@Atharva-Sarnaik`) — primary; Sujal Hede (`@Sujalhede`) — review

---

## Context

Sentinel requires a labelled satellite telemetry dataset with channels that can be defensibly grouped into four subsystems: Power, Thermal, Attitude, and Communications.

The candidate datasets are:

| Dataset | Source | Label type | Access |
|---|---|---|---|
| NASA SMAP | [NASA PO.DAAC](https://podaac.jpl.nasa.gov/) | Point anomaly labels | Public |
| NASA MSL | Same | Point anomaly labels | Public |
| ESA-ADB | ESA Open Data | Contextual anomaly labels | Public |
| OPS-SAT | ESA | Operational telemetry | Public |

**Risk R1:** The SMAP/MSL channel-to-subsystem grouping is unverified. Task T0.5 is a feasibility spike to confirm that a defensible 4-subsystem grouping exists. If it does not, the fallback datasets (ESA-ADB / OPS-SAT) will be used.

---

## Decision

> **To be filled after T0.5 spike completes.**

Currently unresolved. Options:

1. **SMAP + MSL (preferred):** Use NASA SMAP anomaly dataset as primary; MSL as secondary. Channel-to-subsystem map defined in `libs/config/channel_map.yaml`.
2. **ESA-ADB (fallback):** If T0.5 spike shows SMAP/MSL channels cannot be defensibly grouped into four subsystems.
3. **OPS-SAT (fallback):** If ESA-ADB is insufficient.

---

## Consequences

- The chosen dataset determines the channel names in `channel_map.yaml` (risk R1).
- Switching datasets after T0.7 (adapter implementation) would require rework.
- The feasibility spike (T0.5) notebook must document channel-to-subsystem assignments with justification.

---

## References

- Task T0.5: SMAP/MSL feasibility spike
- `libs/config/channel_map.yaml`: channel→subsystem map (placeholder until T0.5)
- ADR-0002: design rules (non-negotiable constraints)

