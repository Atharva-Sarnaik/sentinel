"""
services.audit.log_writer
===========================
Writes immutable AuditEntry records before any downstream outcome is joined.

Backend: SQLite (dev) / PostgreSQL (production).

Design rule (ADR-0002): AuditEntry is written atomically before the
system acts on a decision. It must never be modified after creation.

Owner:   Sujal Hede (@Sujalhede)
Tier:    3 (task T3.5)
Status:  not started
"""

from __future__ import annotations

from libs.contracts import AuditEntry


def write_audit_entry(entry: AuditEntry, db_url: str = "sqlite:///audit.db") -> None:
    """
    Persist an AuditEntry to the audit database.

    Args:
        entry:  The AuditEntry to persist.
        db_url: SQLAlchemy database URL.

    Raises:
        NotImplementedError: Implementation pending task T3.5.
    """
    # TODO (T3.5): implement SQLAlchemy-backed audit log writer.
    raise NotImplementedError("write_audit_entry: implementation pending task T3.5.")
