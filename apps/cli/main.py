"""
apps.cli.main
=============
Typer + Rich command-line interface for Sentinel.

Commands (stubbed, task T5.1):
  sentinel analyze   — run the full multi-agent pipeline on a telemetry file
  sentinel evaluate  — run evaluation arms A–E on a dataset split
  sentinel report    — print or export a results report

Status: scaffolding — all commands raise NotImplementedError.
"""

from __future__ import annotations

import typer
from rich.console import Console

app = typer.Typer(
    name="sentinel",
    help=(
        "Sentinel — Multi-Agent AI System for Satellite Telemetry "
        "Health Monitoring and Anomaly Detection.\n\n"
        "[bold yellow]Status:[/bold yellow] scaffolding, implementation not started."
    ),
    rich_markup_mode="rich",
)
console = Console()


@app.command()
def analyze(
    input_path: str = typer.Argument(..., help="Path to telemetry file or replay source."),
    report: str = typer.Option("none", help="Report format: none | json | html"),
    run_id: str = typer.Option("", help="Optional run ID for audit log."),
) -> None:
    """Run the full multi-agent analysis pipeline on a telemetry source."""
    # TODO (T5.1): implement analyze command.
    raise NotImplementedError("analyze: implementation pending task T5.1.")


@app.command()
def evaluate(
    dataset: str = typer.Argument(..., help="Dataset identifier (e.g. SMAP, MSL)."),
    arms: str = typer.Option("A,B,C,D,E", help="Comma-separated evaluation arms to run."),
) -> None:
    """Run ablation evaluation across all configured arms."""
    # TODO (T5.1 / T4.2): implement evaluate command.
    raise NotImplementedError("evaluate: implementation pending tasks T4.2 and T5.1.")


@app.command()
def report(
    run_id: str = typer.Argument(..., help="Run ID to generate report for."),
    fmt: str = typer.Option("json", help="Output format: json | html"),
) -> None:
    """Export an analysis or evaluation report for a given run ID."""
    # TODO (T5.1 / T5.3): implement report command.
    raise NotImplementedError("report: implementation pending tasks T5.1 and T5.3.")


@app.command()
def specialists_report(
    run_id: str = typer.Argument(..., help="Run ID to report specialist metrics for."),
) -> None:
    """Print per-subsystem specialist metrics table (task T1.8)."""
    # TODO (T1.8): implement specialists report command.
    raise NotImplementedError("specialists_report: implementation pending task T1.8.")


if __name__ == "__main__":
    app()
