# fusion

**Purpose:** Deterministic fusion engine — the sole authority on anomaly severity and alert level.

**Inputs:** List of `libs.contracts.SpecialistOpinion` (all four subsystems).

**Outputs:** `libs.contracts.FusionDecision`.

**Key modules:**
| Module | Description |
|---|---|
| `engine.py` | Severity weighting + fusion (T2.1) |
| `corroboration.py` | Cross-subsystem corroboration rules from config (T2.2) |

**Owner:** Atharva Sarnaik (`@Atharva-Sarnaik`)

**Tier:** 2 | **Tasks:** T2.1, T2.2, T2.3, T2.4

**Status:** `not started`

> **Design rule (ADR-0002):** The LLM never decides severity. The fusion engine decides; the LLM only explains. Same input → same output (deterministic).

