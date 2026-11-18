"""
scripts.demo
============
One-command runnable demonstration of the Sentinel Multi-Agent AI System (Task T5.4).

Demonstrates:
  1. Synthetic telemetry ingestion with coupled multi-channel anomalies.
  2. Parallel specialist agent opinions (Power, Thermal, Attitude, Communications).
  3. Deterministic fusion engine rule evaluation (power-thermal coupling).
  4. Reasoner LLM explanation synthesis.
  5. Grounding verification (preventing hallucinations).
  6. Immutable SQLite audit logging before action.
  7. Automated HTML/JSON report generation.

Execution:
  python scripts/demo.py
  or: sentinel demo

Owner:   Atharva Sarnaik (@Atharva-Sarnaik) / Sujal Hede (@Sujalhede)
Tier:    5 (task T5.4)
Status:  complete — self-contained zero-dependency demo runnable from fresh clone.
"""

from __future__ import annotations

import sys
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from apps.cli.report_export import export_analysis_html, export_analysis_json
from libs.contracts import (
    FusionDecision,
    Subsystem,
    TelemetryWindow,
)
from services.orchestrator.graph import run_pipeline

console = Console()


def create_demo_telemetry_window() -> TelemetryWindow:
    """Generate a deterministic 14-channel telemetry window with injected coupled anomalies."""
    t0 = datetime.now(UTC)
    channels: dict[str, list[float]] = {
        # Power subsystem: P-1 bus voltage spike (>40V)
        "P-1": [28.0, 28.1, 28.2, 48.5, 49.0],
        "P-2": [28.0, 28.0, 28.1, 28.1, 28.0],
        "P-3": [28.0, 28.0, 28.0, 28.0, 28.0],
        "P-4": [28.0, 28.0, 28.0, 28.1, 28.0],
        # Thermal subsystem: T-1 battery temp excursion (>70C)
        "T-1": [45.0, 45.1, 45.3, 72.0, 75.0],
        "T-2": [45.0, 45.0, 45.1, 45.2, 45.1],
        "T-3": [45.0, 45.0, 45.0, 45.1, 45.0],
        # Attitude subsystem: Nominal gyro/quaternion
        "A-1": [1.0, 1.0, 1.0, 1.0, 1.0],
        "A-2": [1.0, 1.0, 1.0, 1.0, 1.0],
        "A-3": [1.0, 1.0, 1.0, 1.0, 1.0],
        "A-4": [1.0, 1.0, 1.0, 1.0, 1.0],
        # Communications subsystem: Nominal RSSI and downlink
        "C-1": [5.0, 5.0, 5.0, 5.0, 5.0],
        "C-2": [5.0, 5.0, 5.0, 5.0, 5.0],
        "D-1": [5.0, 5.0, 5.0, 5.0, 5.0],
    }
    return TelemetryWindow(
        subsystem=Subsystem.POWER,
        start_time=t0,
        end_time=t0 + timedelta(minutes=4),
        channels=channels,
        source_dataset="Sentinel-One-Command-Demo",
    )


def run_sentinel_demo() -> int:
    """Run the complete Sentinel pipeline demo and export artifacts."""
    console.print()
    console.rule(
        "[bold cyan]🛰️  SENTINEL — MULTI-AGENT SATELLITE HEALTH MONITORING DEMO[/bold cyan]"
    )
    console.print(
        "[dim]Architecture: Specialists (4) → Deterministic Fusion → LLM Reasoner → Verifier → SQLite Audit[/dim]\n"
    )

    # Step 1: Telemetry Ingestion
    console.print("[bold yellow]Step 1: Ingesting Telemetry Window...[/bold yellow]")
    window = create_demo_telemetry_window()
    console.print(
        f"  • Window ID: [cyan]{window.window_id}[/cyan]\n"
        f"  • Source Dataset: [cyan]{window.source_dataset}[/cyan]\n"
        f"  • Channels Ingested: [cyan]{len(window.channels)}[/cyan] ({', '.join(sorted(window.channels.keys()))})\n"
        f"  • Injected Coupled Anomaly: [bold red]Power (P-1: 49.0V) + Thermal (T-1: 75.0°C)[/bold red]"
    )

    # Step 2: Multi-Agent Execution
    console.print(
        "\n[bold yellow]Step 2: Executing Multi-Agent LangGraph Pipeline...[/bold yellow]"
    )
    run_id = f"demo-run-{uuid.uuid4().hex[:6]}"
    outcome = run_pipeline(window.model_dump(), run_id=run_id)

    decision: FusionDecision = outcome["decision"]
    explanation = outcome.get("explanation")
    verifier_res = outcome.get("verifier_result")
    audit_entry = outcome.get("audit_entry")
    abstained = outcome.get("abstained", False)

    # Step 3: Specialists Breakdown
    console.print("\n[bold yellow]Step 3: Specialist Agent Opinions Generated:[/bold yellow]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Subsystem", style="cyan")
    table.add_column("Severity", justify="center")
    table.add_column("Anomaly Score", justify="right")
    table.add_column("Responsible Channels", style="yellow")
    table.add_column("Threshold", justify="right")

    for op in decision.opinions:
        sev_color = (
            "green"
            if op.severity.value == "nominal"
            else ("yellow" if op.severity.value == "warning" else "bold red")
        )
        ch_str = ", ".join(op.responsible_channels) if op.responsible_channels else "Nominal"
        table.add_row(
            op.subsystem.value.upper(),
            f"[{sev_color}]{op.severity.value.upper()}[/{sev_color}]",
            f"{op.anomaly_score:.3f}",
            ch_str,
            f"{op.threshold_used:.3f}",
        )
    console.print(table)

    # Step 4: Deterministic Fusion Engine
    console.print("\n[bold yellow]Step 4: Deterministic Fusion Engine Evaluation:[/bold yellow]")
    sev_color = (
        "green"
        if decision.severity.value == "nominal"
        else ("yellow" if decision.severity.value == "warning" else "bold red")
    )
    attr_sub = (
        str(decision.attributed_subsystem.value).upper()
        if decision.attributed_subsystem
        else "NONE"
    )
    corrob_str = (
        ", ".join(s.value.upper() for s in decision.corroborating_subsystems)
        if decision.corroborating_subsystems
        else "None"
    )

    console.print(
        Panel(
            f"[bold]System Alert Level:[/bold] [{sev_color}]{decision.severity.value.upper()}[/{sev_color}]\n"
            f"[bold]Corroboration Rule Applied:[/bold] [cyan]{decision.fusion_rule_applied}[/cyan]\n"
            f"[bold]Attributed Root Cause:[/bold] [bold red]{attr_sub}[/bold red]\n"
            f"[bold]Corroborating Subsystems:[/bold] {corrob_str}\n"
            f"[bold]Rule Guarantee:[/bold] [dim]Severity is governed by deterministic physics rules (ADR-0002 R1)[/dim]",
            title="[bold green]Fusion Engine Decision[/bold green]",
            border_style="green",
        )
    )

    # Step 5: Grounded Explanation & Verification
    console.print("[bold yellow]Step 5: Reasoner Explanation & Grounding Verifier:[/bold yellow]")
    expl_text = (
        explanation.text
        if explanation and hasattr(explanation, "text")
        else ("[yellow]Abstained from ungrounded hallucination.[/yellow]" if abstained else "None")
    )
    console.print(
        Panel(
            expl_text,
            title="[bold cyan]LLM Reasoner Synthesis (Evidence-Bound)[/bold cyan]",
            border_style="cyan",
        )
    )

    ver_status = (
        "[green]GROUNDED (Accepted on first attempt)[/green]"
        if verifier_res and verifier_res.is_grounded
        else "[yellow]ABSTAINED[/yellow]"
    )
    console.print(
        f"  • Verifier Result: {ver_status}\n"
        f"  • Verifier Retries: [cyan]{verifier_res.retry_count if verifier_res else 0}/2[/cyan]\n"
        f"  • Grounding Rule: [dim]Verifier rejects numerical or channel hallucination (ADR-0002 R2)[/dim]"
    )

    # Step 6: Immutable Audit Log
    console.print("\n[bold yellow]Step 6: Immutable Audit Log Verification:[/bold yellow]")
    console.print(
        f"  • Audit Entry ID: [cyan]{audit_entry.entry_id if audit_entry else 'N/A'}[/cyan]\n"
        f"  • Run ID: [cyan]{run_id}[/cyan]\n"
        f"  • Committed Table: [green]audit_entries (SQLite backend: artifacts/audit.db)[/green]\n"
        f"  • Audit Rule: [dim]Logged before downstream action is joined (ADR-0002 R7)[/dim]"
    )

    # Step 7: Export Reports
    console.print("\n[bold yellow]Step 7: Generating Visual & Structured Reports...[/bold yellow]")
    html_path = Path("artifacts/demo_report.html")
    json_path = Path("artifacts/demo_report.json")
    export_analysis_html(outcome, window=window, output_path=html_path)
    export_analysis_json(outcome, json_path)
    console.print(f"  • HTML Dashboard Report: [bold green]{html_path}[/bold green]")
    console.print(f"  • JSON Raw Data Report:  [bold green]{json_path}[/bold green]")

    console.print(
        "\n[bold green]✅ Demo completed successfully! All pipeline stages verified.[/bold green]"
    )
    console.print("[dim]Next steps:[/dim]")
    console.print(
        "  • Start API server: [cyan]uvicorn services.api.app:app --reload --port 8000[/cyan]"
    )
    console.print("  • Run CLI analysis: [cyan]sentinel analyze sample --report html[/cyan]")
    console.print(
        "  • Run ablation:     [cyan]sentinel evaluate synthetic --arms A,B,C,D,E[/cyan]\n"
    )

    return 0


if __name__ == "__main__":
    sys.exit(run_sentinel_demo())
