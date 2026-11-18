"""
apps.cli.report_export
======================
HTML and JSON report generator for Sentinel telemetry analysis and evaluation runs (Task T5.3).

Generates:
  • Standalone responsive HTML reports with styling and health status badges.
  • Structured JSON reports with full fidelity serialization.

Owner:   Sujal Hede (@Sujalhede) / Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    5 (task T5.3)
Status:  complete — validated HTML/JSON analysis and run report exports.
"""

from __future__ import annotations

import html
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from libs.contracts import AuditEntry, FusionDecision, TelemetryWindow


def _json_serial_default(obj: Any) -> Any:
    """Handle custom JSON serialization for UUID, datetime, Enum, and Pydantic models."""
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, "value"):
        return obj.value
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def export_analysis_json(outcome: dict[str, Any], output_path: Path | str) -> Path:
    """
    Export pipeline outcome dictionary to a formatted JSON file.

    Args:
        outcome: Pipeline outcome dictionary from run_pipeline().
        output_path: File path to save the JSON report.

    Returns:
        Path of the saved file.
    """
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(outcome, default=_json_serial_default, indent=2)
    p.write_text(serialized, encoding="utf-8")
    return p


def export_analysis_html(
    outcome: dict[str, Any],
    window: TelemetryWindow | None = None,
    output_path: Path | str = "artifacts/analysis_report.html",
) -> Path:
    """
    Export pipeline outcome dictionary to a standalone HTML report.

    Args:
        outcome: Pipeline outcome dictionary from run_pipeline().
        window: Optional input TelemetryWindow for channel details.
        output_path: Destination file path.

    Returns:
        Path of the saved HTML file.
    """
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)

    decision: FusionDecision | None = outcome.get("decision")
    explanation = outcome.get("explanation")
    verifier_result = outcome.get("verifier_result")
    audit_entry: AuditEntry | None = outcome.get("audit_entry")
    abstained = bool(outcome.get("abstained", False))

    severity_str = decision.severity.value.upper() if decision else "UNKNOWN"
    sev_class = (
        "badge-nominal"
        if severity_str == "NOMINAL"
        else ("badge-warning" if severity_str == "WARNING" else "badge-critical")
    )

    attr_sub = (
        str(decision.attributed_subsystem.value).upper()
        if decision and decision.attributed_subsystem
        else "NONE"
    )
    rule_applied = decision.fusion_rule_applied if decision else "N/A"
    corroborating = (
        ", ".join(s.value.upper() for s in decision.corroborating_subsystems)
        if decision and decision.corroborating_subsystems
        else "None"
    )

    explanation_text = (
        html.escape(explanation.text)
        if explanation and hasattr(explanation, "text")
        else (
            "<i>System abstained from generating an ungrounded explanation.</i>"
            if abstained
            else "No explanation generated."
        )
    )

    opinions_rows = ""
    if decision and decision.opinions:
        for op in decision.opinions:
            sub = op.subsystem.value.upper()
            score = f"{op.anomaly_score:.3f}"
            sev = op.severity.value.upper()
            channels = ", ".join(op.responsible_channels) if op.responsible_channels else "None"
            badge_type = (
                "badge-nominal"
                if sev == "NOMINAL"
                else ("badge-warning" if sev == "WARNING" else "badge-critical")
            )
            opinions_rows += f"""
            <tr>
              <td><strong>{sub}</strong></td>
              <td><span class="badge {badge_type}">{sev}</span></td>
              <td>{score}</td>
              <td><code>{channels}</code></td>
              <td>{op.threshold_used:.3f}</td>
            </tr>
            """
    else:
        opinions_rows = "<tr><td colspan='5'>No specialist opinions available.</td></tr>"

    window_id_str = (
        str(window.window_id) if window else (str(decision.window_id) if decision else "N/A")
    )
    timestamp_str = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%SZ")

    verifier_status = (
        "GROUNDED"
        if verifier_result and verifier_result.is_grounded
        else ("ABSTAINED" if abstained else "UNGROUNDED")
    )
    ver_class = "badge-nominal" if verifier_status == "GROUNDED" else "badge-warning"

    content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Sentinel Telemetry Health Analysis Report</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      margin: 0;
      padding: 30px;
      background: #0d1117;
      color: #c9d1d9;
    }}
    .container {{
      max-width: 960px;
      margin: 0 auto;
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 8px;
      padding: 30px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.5);
    }}
    h1 {{
      color: #58a6ff;
      margin-top: 0;
      font-size: 24px;
      border-bottom: 1px solid #30363d;
      padding-bottom: 12px;
    }}
    h2 {{
      color: #79c0ff;
      font-size: 18px;
      margin-top: 24px;
      margin-bottom: 12px;
    }}
    .badge {{
      display: inline-block;
      padding: 4px 10px;
      font-size: 12px;
      font-weight: bold;
      border-radius: 12px;
      text-transform: uppercase;
    }}
    .badge-nominal {{ background: #238636; color: #ffffff; }}
    .badge-warning {{ background: #d29922; color: #161b22; }}
    .badge-critical {{ background: #da3633; color: #ffffff; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }}
    .card {{
      background: #21262d;
      border: 1px solid #30363d;
      border-radius: 6px;
      padding: 16px;
    }}
    .card-label {{ font-size: 12px; color: #8b949e; text-transform: uppercase; margin-bottom: 6px; }}
    .card-value {{ font-size: 18px; font-weight: 600; color: #f0f6fc; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 16px 0;
      font-size: 14px;
    }}
    th, td {{
      padding: 10px 12px;
      text-align: left;
      border-bottom: 1px solid #30363d;
    }}
    th {{ background: #21262d; color: #8b949e; font-weight: 600; }}
    code {{
      background: rgba(110,118,129,0.4);
      padding: 2px 6px;
      border-radius: 4px;
      font-family: monospace;
      color: #e6edf3;
    }}
    .explanation-box {{
      background: #0d1117;
      border-left: 4px solid #58a6ff;
      padding: 16px;
      border-radius: 0 6px 6px 0;
      font-size: 15px;
      line-height: 1.6;
      color: #e6edf3;
      margin: 16px 0;
    }}
    .footer {{
      margin-top: 30px;
      padding-top: 16px;
      border-top: 1px solid #30363d;
      font-size: 12px;
      color: #8b949e;
      display: flex;
      justify-content: space-between;
    }}
  </style>
</head>
<body>
  <div class="container">
    <h1>SENTINEL — Satellite Telemetry Health Analysis Report</h1>

    <div class="grid">
      <div class="card">
        <div class="card-label">Final System Alert Level</div>
        <div class="card-value"><span class="badge {sev_class}">{severity_str}</span></div>
      </div>
      <div class="card">
        <div class="card-label">Attributed Root Cause</div>
        <div class="card-value">{attr_sub}</div>
      </div>
      <div class="card">
        <div class="card-label">Corroboration Rule</div>
        <div class="card-value">{rule_applied}</div>
      </div>
      <div class="card">
        <div class="card-label">Explanation Grounding</div>
        <div class="card-value"><span class="badge {ver_class}">{verifier_status}</span></div>
      </div>
    </div>

    <h2>Multi-Agent Subsystem Specialist Opinions</h2>
    <table>
      <thead>
        <tr>
          <th>Subsystem</th>
          <th>Severity</th>
          <th>Score</th>
          <th>Responsible Channels</th>
          <th>Calibrated Threshold</th>
        </tr>
      </thead>
      <tbody>
        {opinions_rows}
      </tbody>
    </table>

    <h2>Reasoner Root-Cause Explanation</h2>
    <div class="explanation-box">
      {explanation_text}
    </div>

    <h2>Audit & Integrity Verification</h2>
    <div class="grid">
      <div class="card">
        <div class="card-label">Window ID</div>
        <div class="card-value" style="font-size: 13px;"><code>{window_id_str}</code></div>
      </div>
      <div class="card">
        <div class="card-label">Audit Decision ID</div>
        <div class="card-value" style="font-size: 13px;"><code>{decision.decision_id if decision else "N/A"}</code></div>
      </div>
      <div class="card">
        <div class="card-label">Audit Log Status</div>
        <div class="card-value" style="font-size: 13px;"><code>{"COMMITTED (SQLite)" if audit_entry else "UNCOMMITTED"}</code></div>
      </div>
      <div class="card">
        <div class="card-label">Corroborating Subsystems</div>
        <div class="card-value" style="font-size: 14px;">{corroborating}</div>
      </div>
    </div>

    <div class="footer">
      <span>Generated by Sentinel v0.1.0 (Tier 5 Multi-Agent System)</span>
      <span>Timestamp: {timestamp_str}</span>
    </div>
  </div>
</body>
</html>
"""
    p.write_text(content.strip(), encoding="utf-8")
    return p
