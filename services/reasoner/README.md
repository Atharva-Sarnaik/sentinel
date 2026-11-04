# reasoner

**Purpose:** LLM reasoner — produces structured natural-language explanations from `FusionDecision` evidence.

**Inputs:** `libs.contracts.FusionDecision`.

**Outputs:** `libs.contracts.Explanation`.

**Key modules:**
| Module | Description |
|---|---|
| `reasoner.py` | LLM API call, structured output (T3.2) |
| `schemas.py` | JSON schema for LLM output validation |
| `prompts/explain.txt` | Versioned prompt template |

**Owner:** Atharva Sarnaik (`@Atharva-Sarnaik`)

**Tier:** 3 | **Tasks:** T3.2

**Status:** `not started`

> **Design rule (ADR-0002):** The LLM explains only. It never sets severity. Prompts are versioned files; schema-valid output is enforced. The verifier checks every explanation.

