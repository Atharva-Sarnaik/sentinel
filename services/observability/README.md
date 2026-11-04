# observability

**Purpose:** Langfuse tracing, LLM cost tracking, and latency logging for every inference call.

**Inputs:** LLM call metadata (run ID, model, token counts, latency).

**Outputs:** Traces written to Langfuse; cost and latency summaries available via MLflow.

**Key modules:**
| Module | Description |
|---|---|
| `tracing.py` | Langfuse trace writer (T3.6) |

**Owner:** Atharva Sarnaik (`@Atharva-Sarnaik`)

**Tier:** 3 | **Tasks:** T3.6

**Status:** `not started`

