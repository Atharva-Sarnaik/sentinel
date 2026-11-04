# orchestrator

**Purpose:** LangGraph state graph — orchestrates the full Sentinel pipeline from `TelemetryWindow` to `AuditEntry`.

**Inputs:** `libs.contracts.TelemetryWindow`.

**Outputs:** `libs.contracts.FusionDecision`, `libs.contracts.VerifierResult`, `libs.contracts.AuditEntry`, optional `libs.contracts.Explanation`.

**Pipeline:**
```
TelemetryWindow
  → specialists [parallel]
  → fusion engine
  → LLM reasoner
  → verifier (retry × 2 → abstain)
  → audit log
  → emit
```

**Key modules:**
| Module | Description |
|---|---|
| `graph.py` | LangGraph StateGraph definition and runner |

**Owner:** Atharva Sarnaik (`@Atharva-Sarnaik`)

**Tier:** 3 | **Tasks:** T3.1

**Status:** `not started`

