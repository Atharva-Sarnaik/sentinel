"""
tests.unit.test_cli
===================
Unit tests for Task T5.1 & T5.3: Sentinel Typer CLI (apps.cli.main).

Tests:
  - analyze: sample telemetry input with console output.
  - analyze: report export in JSON and HTML formats.
  - analyze: file not found error handling (exit code 1).
  - evaluate: multi-arm evaluation with table output.
  - report: run manifest reporting with format exports.
  - demo: one-command demo invocation.
  - specialists-report: per-subsystem specialist metrics.

Owner:   Atharva Sarnaik (@Atharva-Sarnaik) / Sujal Hede (@Sujalhede)
Tier:    5 (task T5.1)
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from apps.cli.main import app

runner = CliRunner()


def test_cli_help() -> None:
    """Verify top-level CLI help command displays all subcommands."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Sentinel" in result.stdout
    assert "analyze" in result.stdout
    assert "evaluate" in result.stdout
    assert "report" in result.stdout
    assert "demo" in result.stdout


def test_cli_analyze_sample() -> None:
    """Verify analyze command with 'sample' input executes successfully."""
    result = runner.invoke(app, ["analyze", "sample"])
    assert result.exit_code == 0
    assert "Analysis Summary" in result.stdout
    assert "Specialist Opinions Breakdown" in result.stdout
    assert "POWER" in result.stdout
    assert "THERMAL" in result.stdout
    assert "CRITICAL" in result.stdout


def test_cli_analyze_report_json_and_html(tmp_path: Path) -> None:
    """Verify analyze command exports valid JSON and HTML reports."""
    json_out = tmp_path / "test_out.json"
    result_json = runner.invoke(
        app, ["analyze", "sample", "--report", "json", "--output", str(json_out)]
    )
    assert result_json.exit_code == 0
    assert json_out.is_file()
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert "decision" in payload
    assert "severity" in payload["decision"]

    html_out = tmp_path / "test_out.html"
    result_html = runner.invoke(
        app, ["analyze", "sample", "--report", "html", "--output", str(html_out)]
    )
    assert result_html.exit_code == 0
    assert html_out.is_file()
    html_text = html_out.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in html_text
    assert "SENTINEL" in html_text


def test_cli_analyze_file_not_found() -> None:
    """Verify analyze command handles missing input files cleanly with exit code 1."""
    result = runner.invoke(app, ["analyze", "non_existent_file_9999.json"])
    assert result.exit_code == 1
    assert "Error loading telemetry input" in result.stdout


def test_cli_evaluate_quick() -> None:
    """Verify evaluate command runs requested arms (Arms A and B) and prints table."""
    result = runner.invoke(app, ["evaluate", "synthetic", "--arms", "A,B", "--seed", "42"])
    assert result.exit_code == 0
    assert "Comparative Results Across Experimental Arms" in result.stdout
    assert "Arm A" in result.stdout
    assert "Arm B" in result.stdout


def test_cli_report_command(tmp_path: Path) -> None:
    """Verify report command retrieves run and exports report."""
    report_out = tmp_path / "exp_report.json"
    result = runner.invoke(app, ["report", "latest", "--fmt", "json", "--output", str(report_out)])
    assert result.exit_code == 0
    assert "Report exported successfully" in result.stdout
    assert report_out.is_file()


def test_cli_demo_command() -> None:
    """Verify sentinel demo command executes the full pipeline demo."""
    result = runner.invoke(app, ["demo"])
    assert result.exit_code == 0
    assert "SENTINEL — MULTI-AGENT SATELLITE HEALTH MONITORING DEMO" in result.stdout
    assert "Demo completed successfully!" in result.stdout
