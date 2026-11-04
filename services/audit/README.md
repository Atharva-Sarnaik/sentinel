# audit

**Purpose:** Immutable audit log — records every decision before any downstream outcome is joined.

**Inputs:** `libs.contracts.AuditEntry`.

**Outputs:** Rows in SQLite (dev) or PostgreSQL (production) audit database.

**Key modules:**
| Module | Description |
|---|---|
| `log_writer.py` | SQLAlchemy-backed atomic writer (T3.5) |

**Owner:** Sujal Hede (`@Sujalhede`)

**Tier:** 3 | **Tasks:** T3.5

**Status:** `not started`

> **Design rule (ADR-0002):** AuditEntry is written before the system acts on a decision. It is never modified after creation.

