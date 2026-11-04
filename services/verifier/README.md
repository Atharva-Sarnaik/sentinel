# verifier

**Purpose:** Grounding check — rejects any LLM explanation citing a channel, value or severity not present in the `FusionDecision` evidence. Implements the retry policy and abstention path.

**Inputs:** `libs.contracts.Explanation` + `libs.contracts.FusionDecision`.

**Outputs:** `libs.contracts.VerifierResult`.

**Key modules:**
| Module | Description |
|---|---|
| `grounding.py` | Grounding check (T3.3) |
| `retry.py` | Max-2-retry loop; abstention on failure (T3.4) |

**Owner:** Sujal Hede (`@Sujalhede`) — grounding; Atharva Sarnaik (`@Atharva-Sarnaik`) — retry/abstention

**Tier:** 3 | **Tasks:** T3.3, T3.4

**Status:** `not started`

