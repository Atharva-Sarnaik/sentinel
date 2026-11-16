"""
services.audit.log_writer
===========================
Writes immutable AuditEntry records before any downstream outcome is joined.

Backend: SQLite (standard library sqlite3).

Design rule (ADR-0002):
  • AuditEntry is written atomically before the system acts on a decision.
  • It must never be modified after creation (append-only).

Owner:   Sujal Hede (@Sujalhede) / Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    3 (task T3.5)
Status:  complete — atomic SQLite audit log writer and query interface.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from libs.contracts import AuditEntry, Severity

DEFAULT_AUDIT_DB = "sqlite:///artifacts/audit.db"


def _clean_db_path(db_url_or_path: str) -> str:
    """Extract standard filesystem path from sqlite URL or raw path."""
    if db_url_or_path.startswith("sqlite:///"):
        path_str = db_url_or_path[len("sqlite:///") :]
    elif db_url_or_path.startswith("sqlite://"):
        path_str = db_url_or_path[len("sqlite://") :]
    else:
        path_str = db_url_or_path

    # Handle in-memory database
    if path_str == ":memory:":
        return ":memory:"

    p = Path(path_str)
    p.parent.mkdir(parents=True, exist_ok=True)
    return str(p)


def init_audit_db(db_url_or_path: str = DEFAULT_AUDIT_DB) -> sqlite3.Connection:
    """
    Initialize audit log database table schema.
    """
    db_path = _clean_db_path(db_url_or_path)
    conn = sqlite3.connect(db_path)
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_entries (
                entry_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                window_id TEXT NOT NULL,
                decision_id TEXT NOT NULL,
                verifier_id TEXT NOT NULL,
                final_severity TEXT NOT NULL,
                abstained INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                extra TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_run_id ON audit_entries(run_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_window_id ON audit_entries(window_id)")
    return conn


def write_audit_entry(
    entry: AuditEntry,
    db_url: str = DEFAULT_AUDIT_DB,
) -> None:
    """
    Persist an immutable AuditEntry record to the audit database atomically.

    Args:
        entry: The validated AuditEntry to persist.
        db_url: Database URL or file path (e.g. 'sqlite:///artifacts/audit.db').
    """
    conn = init_audit_db(db_url)
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO audit_entries (
                    entry_id, run_id, window_id, decision_id, verifier_id,
                    final_severity, abstained, created_at, extra
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(entry.entry_id),
                    entry.run_id,
                    str(entry.window_id),
                    str(entry.decision_id),
                    str(entry.verifier_id),
                    entry.final_severity.value,
                    1 if entry.abstained else 0,
                    entry.created_at.isoformat(),
                    json.dumps(entry.extra),
                ),
            )
    finally:
        conn.close()


def get_audit_entry(
    entry_id: str | uuid.UUID,
    db_url: str = DEFAULT_AUDIT_DB,
) -> AuditEntry | None:
    """
    Retrieve an AuditEntry by entry_id.
    """
    conn = init_audit_db(db_url)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT entry_id, run_id, window_id, decision_id, verifier_id,
                   final_severity, abstained, created_at, extra
            FROM audit_entries
            WHERE entry_id = ?
            """,
            (str(entry_id),),
        )
        row = cursor.fetchone()
        if not row:
            return None

        return AuditEntry(
            entry_id=uuid.UUID(row[0]),
            run_id=row[1],
            window_id=uuid.UUID(row[2]),
            decision_id=uuid.UUID(row[3]),
            verifier_id=uuid.UUID(row[4]),
            final_severity=Severity(row[5]),
            abstained=bool(row[6]),
            created_at=datetime.fromisoformat(row[7]),
            extra=json.loads(row[8]),
        )
    finally:
        conn.close()


def list_audit_entries(
    run_id: str | None = None,
    db_url: str = DEFAULT_AUDIT_DB,
) -> list[AuditEntry]:
    """
    List audit entries, optionally filtered by run_id, ordered newest first.
    """
    conn = init_audit_db(db_url)
    try:
        cursor = conn.cursor()
        if run_id:
            cursor.execute(
                """
                SELECT entry_id, run_id, window_id, decision_id, verifier_id,
                       final_severity, abstained, created_at, extra
                FROM audit_entries
                WHERE run_id = ?
                ORDER BY created_at DESC
                """,
                (run_id,),
            )
        else:
            cursor.execute(
                """
                SELECT entry_id, run_id, window_id, decision_id, verifier_id,
                       final_severity, abstained, created_at, extra
                FROM audit_entries
                ORDER BY created_at DESC
                """
            )

        entries: list[AuditEntry] = []
        for row in cursor.fetchall():
            entries.append(
                AuditEntry(
                    entry_id=uuid.UUID(row[0]),
                    run_id=row[1],
                    window_id=uuid.UUID(row[2]),
                    decision_id=uuid.UUID(row[3]),
                    verifier_id=uuid.UUID(row[4]),
                    final_severity=Severity(row[5]),
                    abstained=bool(row[6]),
                    created_at=datetime.fromisoformat(row[7]),
                    extra=json.loads(row[8]),
                )
            )
        return entries
    finally:
        conn.close()
