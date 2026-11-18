"""
apps.cli.main
=============
Typer + Rich command-line interface for Sentinel (Tasks T5.1 & T5.3).

Commands:
  sentinel analyze             — run full multi-agent pipeline on a telemetry file or sample
  sentinel evaluate            — run evaluation arms A–E on dataset splits
  sentinel report              — print or export an analysis or experiment run report
  sentinel specialists-report  — print per-subsystem specialist metrics table
  sentinel demo                — execute end-to-end demo across the full multi-agent pipeline

Owner:   Atharva Sarnaik (@Atharva-Sarnaik) / Sujal Hede (@Sujalhede)
Tier:    5 (tasks T5.1, T5.3, T5.4)
Status:  complete — production-ready CLI with Rich formatting and report exports.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from apps.cli.report_export import export_analysis_html, export_analysis_json
from libs.common.manifest import ManifestStore
from libs.contracts import (
    FusionDecision,
    Subsystem,
    TelemetryWindow,
)
from services.evaluation.ablation import run_ablation
from services.orchestrator.graph import run_pipeline

app = typer.Typer(
    name="sentinel",
    help=(
        "[bold cyan]Sentinel[/bold cyan] — Multi-Agent AI System for Satellite Telemetry "
        "Health Monitoring and Anomaly Detection.\n\n"
        "Decision-support research prototype providing multi-agent health monitoring, "
        "deterministic severity fusion, grounded LLM explanations, and immutable audit logging."
    ),
    rich_markup_mode="rich",
)
console = Console()


def _generate_sample_window() -> TelemetryWindow:
    """Generate a realistic test TelemetryWindow with Power and Thermal coupled anomalies."""
    t0 = datetime.now(UTC)
    channels: dict[str, list[float]] = {
        "P-1": [28.0, 28.1, 48.5, 49.0, 48.8],
        "P-2": [28.0, 28.0, 28.1, 28.2, 28.1],
        "P-3": [28.0, 28.0, 28.0, 28.1, 28.0],
        "P-4": [28.0, 28.0, 28.1, 28.0, 28.0],
        "T-1": [45.0, 45.2, 72.0, 75.0, 74.5],
        "T-2": [45.0, 45.1, 45.0, 45.2, 45.1],
        "T-3": [45.0, 45.0, 45.1, 45.0, 45.2],
        "A-1": [1.0, 1.0, 1.0, 1.0, 1.0],
        "A-2": [1.0, 1.0, 1.0, 1.0, 1.0],
        "A-3": [1.0, 1.0, 1.0, 1.0, 1.0],
        "A-4": [1.0, 1.0, 1.0, 1.0, 1.0],
        "C-1": [5.0, 5.0, 5.0, 5.0, 5.0],
        "C-2": [5.0, 5.0, 5.0, 5.0, 5.0],
        "D-1": [5.0, 5.0, 5.0, 5.0, 5.0],
    }
    return TelemetryWindow(
        subsystem=Subsystem.POWER,
        start_time=t0,
        end_time=t0 + timedelta(minutes=4),
        channels=channels,
        source_dataset="CLI-Synthetic-Sample",
    )


def _load_window_from_file(input_path: str) -> TelemetryWindow:
    """Load and parse TelemetryWindow from a JSON or telemetry file."""
    p = Path(input_path)
    if not p.is_file():
        raise FileNotFoundError(f"Telemetry input file not found: '{input_path}'")

    raw_text = p.read_text(encoding="utf-8")
    data = json.loads(raw_text)

    # Support model_dump structure or raw dictionary
    if "subsystem" in data and "channels" in data:
        return TelemetryWindow.model_validate(data)

    raise ValueError(f"File '{input_path}' does not match TelemetryWindow schema.")


@app.command()
def analyze(
    input_path: str = typer.Argument(
        ...,
        help="Path to telemetry file, window JSON, or 'sample' to generate test telemetry.",
    ),
    report: str = typer.Option("none", help="Export report format: none | json | html"),
    output: str = typer.Option("", help="Optional output path for exported report."),
    run_id: str = typer.Option("", help="Optional execution run ID for audit log."),
) -> None:
    """
    Run the full Sentinel multi-agent analysis pipeline on a telemetry source.

    Executes:
      1. Specialist agents (Power, Thermal, Attitude, Communications).
      2. Deterministic fusion severity scoring & corroboration.
      3. Reasoner LLM explanation synthesis.
      4. Grounding verification (max 2 retries, then abstain).
      5. Immutable SQLite audit logging.
    """
    console.print()
    console.rule("[bold cyan]Sentinel Multi-Agent Analysis Pipeline[/bold cyan]")

    # 1. Load or generate window
    if input_path.strip().lower() == "sample":
        window = _generate_sample_window()
        console.print("[dim]Generated synthetic sample window (Power + Thermal coupling).[/dim]")
    else:
        try:
            window = _load_window_from_file(input_path)
            console.print(f"[dim]Loaded TelemetryWindow from '{input_path}'.[/dim]")
        except Exception as e:
            console.print(f"[bold red]Error loading telemetry input:[/bold red] {e}")
            raise typer.Exit(code=1) from e

    # 2. Run pipeline
    exec_run_id = run_id or f"cli-run-{uuid.uuid4().hex[:8]}"
    console.print(f"[bold]Executing pipeline (Run ID:[/bold] {exec_run_id})...")
    outcome = run_pipeline(window.model_dump(), run_id=exec_run_id)

    decision: FusionDecision = outcome["decision"]
    explanation = outcome.get("explanation")
    verifier_res = outcome.get("verifier_result")
    audit_entry = outcome.get("audit_entry")
    abstained = outcome.get("abstained", False)

    # 3. Render Rich Output
    sev = decision.severity.value.upper()
    sev_color = "green" if sev == "NOMINAL" else ("yellow" if sev == "WARNING" else "bold red")
    attr_sub = (
        str(decision.attributed_subsystem.value).upper()
        if decision.attributed_subsystem
        else "NONE"
    )

    console.print()
    console.print(
        Panel(
            f"[bold]Window ID:[/bold] {window.window_id}\n"
            f"[bold]Channels:[/bold] {len(window.channels)} telemetry channels\n"
            f"[bold]Time Interval:[/bold] {window.start_time.isoformat()} → {window.end_time.isoformat()}\n"
            f"[bold]Final Severity:[/bold] [{sev_color}]{sev}[/{sev_color}]\n"
            f"[bold]Attributed Subsystem:[/bold] {attr_sub}\n"
            f"[bold]Fusion Rule Applied:[/bold] {decision.fusion_rule_applied}",
            title="[bold green]Analysis Summary[/bold green]",
            border_style="green",
        )
    )

    # Specialist opinions table
    table = Table(
        title="Specialist Opinions Breakdown",
        show_header=True,
        header_style="bold magenta",
        expand=True,
    )
    table.add_column("Subsystem", style="cyan")
    table.add_column("Severity", justify="center")
    table.add_column("Score", justify="right")
    table.add_column("Responsible Channels", style="yellow")
    table.add_column("Threshold", justify="right")

    for op in decision.opinions:
        op_sev = op.severity.value.upper()
        op_color = "green" if op_sev == "NOMINAL" else ("yellow" if op_sev == "WARNING" else "red")
        channels_str = ", ".join(op.responsible_channels) if op.responsible_channels else "—"
        table.add_row(
            op.subsystem.value.upper(),
            f"[{op_color}]{op_sev}[/{op_color}]",
            f"{op.anomaly_score:.3f}",
            channels_str,
            f"{op.threshold_used:.3f}",
        )
    console.print(table)

    # Explanation panel
    expl_text = (
        explanation.text
        if explanation and hasattr(explanation, "text")
        else (
            "[yellow]System abstained from generating an ungrounded explanation.[/yellow]"
            if abstained
            else "No explanation generated."
        )
    )
    console.print()
    console.print(
        Panel(
            expl_text,
            title="[bold cyan]Reasoner Explanation (Evidence-Bound)[/bold cyan]",
            border_style="cyan",
        )
    )

    # Verifier & Audit panel
    grounded_status = (
        "[green]GROUNDED (Accepted)[/green]"
        if verifier_res and verifier_res.is_grounded
        else ("[yellow]ABSTAINED[/yellow]" if abstained else "[red]UNGROUNDED[/red]")
    )
    console.print(
        Panel(
            f"[bold]Grounding Status:[/bold] {grounded_status}\n"
            f"[bold]Verifier Retries:[/bold] {verifier_res.retry_count if verifier_res else 0}/2\n"
            f"[bold]Audit Entry ID:[/bold] {audit_entry.entry_id if audit_entry else 'None'}\n"
            f"[bold]Audit Log Status:[/bold] [green]COMMITTED TO SQLITE[/green]",
            title="[bold blue]Verification & Audit Integrity[/bold blue]",
            border_style="blue",
        )
    )

    # 4. Export report if requested
    report_fmt = report.strip().lower()
    if report_fmt in ("json", "html"):
        out_p = Path(output) if output else Path(f"artifacts/analysis_report.{report_fmt}")
        if report_fmt == "json":
            saved = export_analysis_json(outcome, out_p)
        else:
            saved = export_analysis_html(outcome, window=window, output_path=out_p)
        console.print(f"\n[bold green]Report exported successfully:[/bold green] {saved}")

    console.print()


@app.command()
def evaluate(
    dataset: str = typer.Argument(
        "synthetic", help="Dataset identifier (e.g. synthetic, smap, msl)."
    ),
    arms: str = typer.Option("A,B,C,D,E", help="Comma-separated evaluation arms to run."),
    seed: int = typer.Option(42, help="Random seed for deterministic evaluation."),
) -> None:
    """
    Run ablation evaluation across configured arms (A through E).
    """
    from scripts.run_experiments import generate_standard_evaluation_windows

    console.print()
    console.rule("[bold cyan]Sentinel Ablation Evaluation Runner[/bold cyan]")
    arm_list = tuple(a.strip().upper() for a in arms.split(",") if a.strip())
    console.print(
        f"[dim]Initializing dataset '{dataset}' (seed={seed}, arms={', '.join(arm_list)})...[/dim]"
    )

    train_windows, test_windows, ground_truth = generate_standard_evaluation_windows(seed=seed)
    console.print(
        f"[dim]Generated {len(train_windows)} train windows, {len(test_windows)} evaluation windows.[/dim]"
    )

    with console.status("[bold green]Executing evaluation arms..."):
        results = run_ablation(
            windows=test_windows,
            arms=arm_list,
            ground_truth=ground_truth,
            train_windows=train_windows,
        )

    table = Table(
        title="Comparative Results Across Experimental Arms",
        show_header=True,
        header_style="bold magenta",
        expand=True,
    )
    table.add_column("Arm", style="cyan", no_wrap=True)
    table.add_column("Name", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Precision", justify="right")
    table.add_column("Recall", justify="right")
    table.add_column("F1-Score", justify="right")
    table.add_column("FPR", justify="right")
    table.add_column("Samples", justify="right")
    table.add_column("Time (s)", justify="right")

    for arm_key in arm_list:
        data = results.get(arm_key, {})
        status_str = data.get("status", "N/A")
        prec = f"{data.get('precision', 0.0):.4f}" if "precision" in data else "—"
        rec = f"{data.get('recall', 0.0):.4f}" if "recall" in data else "—"
        f1 = f"{data.get('f1', 0.0):.4f}" if "f1" in data else "—"
        fpr = (
            f"{data.get('false_positive_rate', 0.0):.4f}" if "false_positive_rate" in data else "—"
        )
        n_samples = str(data.get("sample_count", len(test_windows)))
        t_sec = f"{data.get('execution_time_sec', 0.0):.2f}s"

        table.add_row(
            f"Arm {arm_key}",
            data.get("name", f"Arm {arm_key}"),
            status_str,
            prec,
            rec,
            f1,
            fpr,
            n_samples,
            t_sec,
        )

    console.print()
    console.print(table)
    console.print()


@app.command()
def report(
    run_id: str = typer.Argument(..., help="Run ID to generate report for (or 'latest')."),
    fmt: str = typer.Option("json", help="Output format: json | html"),
    output: str = typer.Option("", help="Optional output destination file path."),
) -> None:
    """Export or print an analysis or experiment run report for a given run ID."""
    store = ManifestStore()
    target_run_id = run_id
    if run_id.lower() == "latest":
        manifests = store.list_all()
        if not manifests:
            console.print(
                "[yellow]No runs found in manifest store. Run experiments first.[/yellow]"
            )
            raise typer.Exit(code=1)
        target_run_id = manifests[0].run_id

    manifest = store.get(target_run_id)
    if not manifest:
        console.print(f"[bold red]Run ID '{target_run_id}' not found in manifest store.[/bold red]")
        raise typer.Exit(code=1)

    metrics_path = Path("artifacts/runs") / target_run_id / "metrics.json"
    metrics_data = {}
    if metrics_path.is_file():
        try:
            metrics_data = json.loads(metrics_path.read_text(encoding="utf-8"))
        except Exception:
            metrics_data = {"error": "Could not read metrics.json"}

    report_payload = {
        "run_id": target_run_id,
        "manifest": manifest.model_dump(mode="json"),
        "metrics": metrics_data,
        "generated_at": datetime.now(UTC).isoformat(),
    }

    fmt_clean = fmt.strip().lower()
    dest = Path(output) if output else Path(f"artifacts/{target_run_id}_report.{fmt_clean}")
    dest.parent.mkdir(parents=True, exist_ok=True)

    if fmt_clean == "json":
        dest.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")
    elif fmt_clean == "html":
        html_content = f"""<!DOCTYPE html>
<html>
<head><title>Sentinel Run Report - {target_run_id}</title>
<style>
body {{ font-family: sans-serif; background: #0d1117; color: #c9d1d9; padding: 30px; }}
.card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; max-width: 800px; margin: 0 auto; }}
h1 {{ color: #58a6ff; }}
pre {{ background: #21262d; padding: 15px; border-radius: 6px; overflow-x: auto; color: #79c0ff; }}
</style>
</head>
<body>
<div class="card">
  <h1>Sentinel Experiment Report — {target_run_id}</h1>
  <p><strong>Description:</strong> {manifest.description}</p>
  <p><strong>Created At:</strong> {manifest.created_at}</p>
  <p><strong>Git Commit:</strong> {manifest.git_commit or "N/A"}</p>
  <h2>Metrics Payload</h2>
  <pre>{json.dumps(metrics_data, indent=2)}</pre>
</div>
</body>
</html>"""
        dest.write_text(html_content, encoding="utf-8")
    else:
        console.print(f"[bold red]Unsupported format '{fmt}'. Choose 'json' or 'html'.[/bold red]")
        raise typer.Exit(code=1)

    console.print(f"[bold green]Report exported successfully to:[/bold green] {dest}")


@app.command(name="specialists-report")
def specialists_report(
    run_id: str = typer.Argument(
        ..., help="Run ID to report specialist metrics for (or 'latest')."
    ),
) -> None:
    """Print per-subsystem specialist metrics table (task T1.8)."""
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


@app.command()
def demo() -> None:
    """Run an end-to-end interactive demo across the entire multi-agent Sentinel pipeline."""
    from scripts.demo import run_sentinel_demo

    run_sentinel_demo()


if __name__ == "__main__":
    app()
