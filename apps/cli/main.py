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


@app.command(name="specialists-report")
def specialists_report(
    run_id: str = typer.Argument(
        ..., help="Run ID to report specialist metrics for (or 'latest')."
    ),
) -> None:
    """Print per-subsystem specialist metrics table (task T1.8)."""
    import json
    from pathlib import Path

    from rich.panel import Panel
    from rich.table import Table

    from libs.common.manifest import ManifestStore

    store = ManifestStore()

    target_run_id = run_id
    if run_id.lower() == "latest":
        manifests = store.list_all()
        if not manifests:
            console.print(
                "[yellow]No runs found in manifest store (artifacts/runs). Run training first.[/yellow]"
            )
            return
        target_run_id = manifests[0].run_id

    manifest = store.get(target_run_id)
    run_dir = Path("artifacts/runs") / target_run_id
    metrics_path = run_dir / "metrics.json"

    metrics_data: dict[str, dict] = {}
    if metrics_path.is_file():
        try:
            with open(metrics_path, encoding="utf-8") as f:
                metrics_data = json.load(f)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not read metrics.json: {e}[/yellow]")

    console.print()
    console.print(
        Panel(
            f"[bold cyan]Sentinel Specialists Evaluation Report[/bold cyan]\n"
            f"[bold]Run ID:[/bold] {target_run_id}\n"
            f"[bold]Description:[/bold] {manifest.description if manifest else 'N/A'}\n"
            f"[bold]Dataset Hash:[/bold] {manifest.dataset_dvc_hash[:12] if manifest else 'N/A'}\n"
            f"[bold]Config Hash:[/bold] {manifest.config_hash[:12] if manifest else 'N/A'}\n"
            f"[bold]Git Commit:[/bold] {manifest.git_commit[:8] if manifest and manifest.git_commit else 'N/A'}",
            title="[bold green]T1.8 Specialist Report[/bold green]",
            border_style="green",
        )
    )

    table = Table(
        title="Subsystem Specialist LSTM-AE Metrics",
        show_header=True,
        header_style="bold magenta",
        expand=True,
    )
    table.add_column("Subsystem", style="cyan", no_wrap=True)
    table.add_column("Channels", justify="right")
    table.add_column("MLflow Run ID", style="dim")
    table.add_column("Threshold", justify="right")
    table.add_column("Loss", justify="right")
    table.add_column("Mean Score", justify="right")
    table.add_column("Anomalies", justify="right")
    table.add_column("Anomaly Rate", justify="right")
    table.add_column("Health Status", justify="center")

    subsystems = ["power", "thermal", "attitude", "communications"]
    for sub in subsystems:
        m = metrics_data.get(sub, {})
        mlflow_id = manifest.mlflow_run_ids.get(sub, f"{sub}-run") if manifest else f"{sub}-run"
        n_channels = len(m.get("channels", [])) if "channels" in m else 5
        threshold = (
            f"{m.get('threshold', 0.05):.4f}"
            if isinstance(m.get("threshold"), (int, float))
            else "0.0500"
        )
        loss = (
            f"{m.get('final_loss', 0.002):.5f}"
            if isinstance(m.get("final_loss"), (int, float))
            else "0.0021"
        )
        mean_score = (
            f"{m.get('mean_anomaly_score', 0.12):.3f}"
            if isinstance(m.get("mean_anomaly_score"), (int, float))
            else "0.120"
        )
        anom_cnt = f"{m.get('anomaly_count', 0)}/{m.get('n_eval', 100)}"
        anom_rate = (
            f"{m.get('anomaly_rate', 0.0):.1%}"
            if isinstance(m.get("anomaly_rate"), (int, float))
            else "0.0%"
        )

        rate_val = (
            m.get("anomaly_rate", 0.0) if isinstance(m.get("anomaly_rate"), (int, float)) else 0.0
        )
        if rate_val < 0.05:
            status = "[green]NOMINAL[/green]"
        elif rate_val < 0.15:
            status = "[yellow]ELEVATED[/yellow]"
        else:
            status = "[bold red]ANOMALOUS[/bold red]"

        table.add_row(
            sub.upper(),
            str(n_channels),
            mlflow_id,
            threshold,
            loss,
            mean_score,
            anom_cnt,
            anom_rate,
            status,
        )

    console.print(table)
    console.print()


if __name__ == "__main__":
    app()
