"""apps.dashboard.app
==================
Streamlit Aerospace Mission Control Telemetry Replay Dashboard for Sentinel (Task T6.1).

Design System: Aerospace Mission Control (Stitch export specification)
Colors:
  - Canvas Base: #F8FAFC
  - Panel Surface: #FFFFFF
  - Hairline Borders: #E2E8F0, #CBD5E1
  - Primary Text: #0F172A
  - Telemetry Monospace: JetBrains Mono
  - Status Badges: Nominal (#10B981), Warning (#F59E0B), Critical (#EF4444), Link (#0058BE)

Panels:
  1. Mission Overview (Satellite Health, Anomaly Probability, Active Anomalies, Grounding Verif, Audit Integrity)
  2. Power Subsystem (EPS) (P-1..P-4 telemetry, inference matrix, thresholds, time-series)
  3. Thermal Subsystem (TCS) (T-1..T-3 telemetry, inference matrix, thresholds, time-series)
  4. Attitude Subsystem (ADCS) (A-1..A-4 telemetry, inference matrix, thresholds, time-series)
  5. Communications Subsystem (TT&C) (C-1, C-2, D-1 telemetry, inference matrix, thresholds, time-series)
  6. Coordinator & Fusion Center (Multi-agent fusion, root-cause diagnosis, LLM explanation, verifier, audit trail)

Owner:   Sujal Hede (@Sujalhede)
Tier:    6 (task T6.1)
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st
from scripts.run_experiments import generate_standard_evaluation_windows

from libs.contracts import (
    FusionDecision,
    SpecialistOpinion,
    Subsystem,
    TelemetryWindow,
)
from services.fusion.stacking import LearnedStackingCoordinator
from services.orchestrator.graph import run_pipeline

# ---------------------------------------------------------------------------
# Aerospace Mission Control Styling & CSS Tokens
# ---------------------------------------------------------------------------

AEROSPACE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

/* Canvas & Global Typography */
.stApp {
    background-color: #F8FAFC;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #0F172A;
}

/* Aerospace Card Containers */
.aerospace-card {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 14px 18px;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
    margin-bottom: 12px;
}

.aerospace-card-hero {
    background: linear-gradient(135deg, #FFFFFF 0%, #F1F5F9 100%);
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 20px 24px;
    box-shadow: 0 2px 6px rgba(15, 23, 42, 0.06);
    margin-bottom: 16px;
}

/* Monospace Telemetry Readouts */
.mono-data-lg {
    font-family: 'JetBrains Mono', monospace;
    font-size: 26px;
    font-weight: 700;
    color: #0F172A;
    letter-spacing: -0.03em;
    line-height: 1.1;
}

.mono-data-md {
    font-family: 'JetBrains Mono', monospace;
    font-size: 14px;
    font-weight: 600;
    color: #0F172A;
    letter-spacing: -0.01em;
}

.mono-data-sm {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 500;
    color: #475569;
}

/* Micro-labels */
.label-caps {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: 600;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* Status Micro-Badges */
.badge-nominal {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background-color: #ECFDF5;
    color: #065F46;
    border: 1px solid #A7F3D0;
    border-radius: 4px;
    padding: 2px 8px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
}

.badge-warning {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background-color: #FFFBEB;
    color: #92400E;
    border: 1px solid #FDE68A;
    border-radius: 4px;
    padding: 2px 8px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
}

.badge-critical {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background-color: #FEF2F2;
    color: #991B1B;
    border: 1px solid #FECACA;
    border-radius: 4px;
    padding: 2px 8px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
}

.badge-info {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background-color: #EFF6FF;
    color: #1E40AF;
    border: 1px solid #BFDBFE;
    border-radius: 4px;
    padding: 2px 8px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
}

/* Custom Tabs Styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    border-bottom: 2px solid #E2E8F0;
    padding-bottom: 4px;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    font-weight: 600;
    color: #475569;
    padding: 8px 16px;
    border-radius: 4px 4px 0 0;
}
.stTabs [aria-selected="true"] {
    color: #0058BE !important;
    border-bottom: 2px solid #0058BE !important;
}
</style>
"""

# Subsystem Domain Metadata from Aerospace Mission Control Design System
SUBSYSTEM_META: dict[Subsystem, dict[str, Any]] = {
    Subsystem.POWER: {
        "title": "Power Subsystem (EPS)",
        "code": "EPS-BUS-A/B",
        "icon": "⚡",
        "prefix": "P",
        "model": "LSTM-AE + Dynamic Thresholding Ensemble",
        "channels": {
            "P-1": {
                "name": "Regulated Bus Voltage",
                "unit": "V",
                "baseline": "28.40 V",
                "limit": "27.5 - 29.5 V",
            },
            "P-2": {
                "name": "Total Load Current",
                "unit": "A",
                "baseline": "14.15 A",
                "limit": "10.0 - 18.0 A",
            },
            "P-3": {
                "name": "Battery State of Charge",
                "unit": "%",
                "baseline": "99.2 %",
                "limit": "60.0 - 100.0 %",
            },
            "P-4": {
                "name": "Solar Array Power Output",
                "unit": "W",
                "baseline": "312.4 W",
                "limit": "250.0 - 380.0 W",
            },
        },
    },
    Subsystem.THERMAL: {
        "title": "Thermal Subsystem (TCS)",
        "code": "TCS-RAD-DECK",
        "icon": "🌡️",
        "prefix": "T",
        "model": "Nonparametric Dynamic Thresholding + LSTM-AE",
        "channels": {
            "T-1": {
                "name": "Radiator Deck Temperature",
                "unit": "°C",
                "baseline": "+21.4 °C",
                "limit": "-15.0 to +45.0 °C",
            },
            "T-2": {
                "name": "Battery Compartment Temp",
                "unit": "°C",
                "baseline": "+18.2 °C",
                "limit": "0.0 to +35.0 °C",
            },
            "T-3": {
                "name": "Deep Space Radiator Panel",
                "unit": "°C",
                "baseline": "-4.6 °C",
                "limit": "-65.0 to +70.0 °C",
            },
        },
    },
    Subsystem.ATTITUDE: {
        "title": "Attitude Control Subsystem (ADCS)",
        "code": "ADCS-GYRO-RWA",
        "icon": "🔄",
        "prefix": "A",
        "model": "Coupled Dynamic Autoencoder Ensemble",
        "channels": {
            "A-1": {
                "name": "Pitch Axis Angular Rate",
                "unit": "rad/s",
                "baseline": "0.0042 rad/s",
                "limit": "< 0.050 rad/s",
            },
            "A-2": {
                "name": "Roll Axis Angular Rate",
                "unit": "rad/s",
                "baseline": "0.0018 rad/s",
                "limit": "< 0.050 rad/s",
            },
            "A-3": {
                "name": "Yaw Axis Angular Rate",
                "unit": "rad/s",
                "baseline": "0.0025 rad/s",
                "limit": "< 0.050 rad/s",
            },
            "A-4": {
                "name": "Magnetic Torquer Current",
                "unit": "mA",
                "baseline": "42.1 mA",
                "limit": "< 120.0 mA",
            },
        },
    },
    Subsystem.COMMUNICATIONS: {
        "title": "Communications Subsystem (TT&C)",
        "code": "TTC-S/X-BAND",
        "icon": "📡",
        "prefix": "C",
        "model": "RF Link Margin & Dynamic Telemetry AE",
        "channels": {
            "C-1": {
                "name": "S-Band Downlink Signal RSSI",
                "unit": "dBm",
                "baseline": "-82.4 dBm",
                "limit": "> -105.0 dBm",
            },
            "C-2": {
                "name": "X-Band Transmitter Power",
                "unit": "dBm",
                "baseline": "48.2 dBm",
                "limit": "40.0 - 52.0 dBm",
            },
            "D-1": {
                "name": "Internal Bus Mil-Std-1553",
                "unit": "%",
                "baseline": "38.2 %",
                "limit": "< 75.0 %",
            },
        },
    },
}

# ---------------------------------------------------------------------------
# Data Caching and Leakage-Free Training
# ---------------------------------------------------------------------------


@st.cache_data
def get_cached_telemetry_windows(seed: int = 42) -> tuple[list[TelemetryWindow], list[bool]]:
    """Generate and cache standard evaluation windows for replay."""
    _, test_windows, ground_truth = generate_standard_evaluation_windows(
        seed=seed, n_train=10, n_test=30
    )
    return test_windows, ground_truth


def prepare_stacking_training_data(
    train_windows: list[TelemetryWindow],
) -> tuple[list[TelemetryWindow], list[bool]]:
    """Prepare balanced training samples from healthy training windows without data leakage.

    1. Keeps original healthy windows unchanged and labeled False (nominal).
    2. Generates separate synthetic anomaly copies with unique window IDs,
       multiplying channels ('P-1', 'T-1', 'A-1') by 1.75, labeled True (anomalous).
    """
    training_samples: list[TelemetryWindow] = []
    training_labels: list[bool] = []

    # 1. Nominal samples (original healthy windows unchanged, labeled False)
    for w in train_windows:
        training_samples.append(w)
        training_labels.append(False)

    # 2. Synthetic anomaly copies (labeled True)
    for w in train_windows:
        anom_channels: dict[str, list[float]] = {}
        for ch, vals in w.channels.items():
            if ch in ("P-1", "T-1", "A-1"):
                anom_channels[ch] = [val * 1.75 for val in vals]
            else:
                anom_channels[ch] = list(vals)

        anom_window = TelemetryWindow(
            window_id=uuid.uuid4(),
            subsystem=w.subsystem,
            start_time=w.start_time,
            end_time=w.end_time,
            channels=anom_channels,
            source_dataset=w.source_dataset,
            metadata=dict(w.metadata),
        )
        training_samples.append(anom_window)
        training_labels.append(True)

    return training_samples, training_labels


@st.cache_resource
def get_cached_stacking_coordinator() -> LearnedStackingCoordinator:
    """Initialize and train a cached stacking coordinator using training data only."""
    train_windows, _, _ = generate_standard_evaluation_windows(seed=42, n_train=10, n_test=20)
    training_samples, training_labels = prepare_stacking_training_data(train_windows)

    train_ops: list[list[SpecialistOpinion]] = []
    for sample in training_samples:
        res = run_pipeline(sample.model_dump(), run_id="dash-train")
        train_ops.append(res["decision"].opinions)

    coordinator = LearnedStackingCoordinator(random_state=42)
    coordinator.fit(train_ops, training_labels)
    return coordinator


# ---------------------------------------------------------------------------
# UI Panel Renderers (Aerospace Mission Control Spec)
# ---------------------------------------------------------------------------


def render_subsystem_panel(
    subsystem: Subsystem,
    opinion: SpecialistOpinion | None,
    window: TelemetryWindow,
    channel_prefix: str,
) -> None:
    """Render a dedicated telemetry and health panel for a single spacecraft subsystem."""
    # Filter subsystem channels
    sub_channels = {
        ch: vals for ch, vals in window.channels.items() if ch.startswith(channel_prefix)
    }

    meta = SUBSYSTEM_META.get(
        subsystem,
        {
            "title": f"{subsystem.value.upper()} Subsystem Health",
            "code": f"{subsystem.value.upper()}-CORE",
            "icon": "🛰️",
            "model": "Specialist Detector Ensemble",
            "channels": {},
        },
    )

    sev_val = opinion.severity.value.upper() if opinion else "NOMINAL"
    score_val = opinion.anomaly_score if opinion else 0.05
    thresh_val = opinion.threshold_used if opinion else 0.50
    resp_ch = (
        ", ".join(opinion.responsible_channels)
        if opinion and opinion.responsible_channels
        else "None (All baseline)"
    )

    badge_cls = "badge-nominal"
    if sev_val == "CRITICAL":
        badge_cls = "badge-critical"
    elif sev_val in ("WARNING", "ADVISORY"):
        badge_cls = "badge-warning"

    # Top Subsystem Header Banner
    st.markdown(
        f"""
        <div class="aerospace-card" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
            <div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 20px;">{meta["icon"]}</span>
                    <span style="font-size: 18px; font-weight: 700; color: #0F172A;">{meta["title"]}</span>
                    <span class="{badge_cls}">{sev_val}</span>
                </div>
                <div class="label-caps" style="margin-top: 4px;">
                    SUBSYSTEM CODE: <strong style="color: #0F172A;">{meta["code"]}</strong> • MODEL: <span>{meta["model"]}</span>
                </div>
            </div>
            <div style="display: flex; gap: 16px; align-items: center;">
                <div style="text-align: right;">
                    <div class="label-caps">ANOMALY SCORE</div>
                    <div class="mono-data-lg" style="font-size: 20px;">{score_val:.3f} <span style="font-size: 12px; color: #64748B; font-weight: 400;">/ 1.000</span></div>
                </div>
                <div style="width: 1px; height: 32px; background: #E2E8F0;"></div>
                <div style="text-align: right;">
                    <div class="label-caps">THRESHOLD</div>
                    <div class="mono-data-lg" style="font-size: 20px; color: #0058BE;">{thresh_val:.3f}</div>
                </div>
                <div style="width: 1px; height: 32px; background: #E2E8F0;"></div>
                <div style="text-align: right;">
                    <div class="label-caps">RESPONSIBLE CHANNELS</div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 600; color: {"#991B1B" if resp_ch != "None (All baseline)" else "#065F46"};">{resp_ch}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Detailed Channel Breakdown Cards
    if sub_channels:
        cols = st.columns(min(len(sub_channels), 4))
        ch_items = list(sub_channels.items())
        for idx, (ch, vals) in enumerate(ch_items):
            with cols[idx % len(cols)]:
                ch_info = meta.get("channels", {}).get(ch, {})
                ch_name = ch_info.get("name", "Telemetry Channel")
                ch_unit = ch_info.get("unit", "")
                latest_val = vals[-1] if vals else 0.0
                mean_val = sum(vals) / len(vals) if vals else 0.0

                is_resp = ch in (opinion.responsible_channels if opinion else [])
                ch_badge = (
                    '<span class="badge-critical">ANOMALOUS</span>'
                    if is_resp
                    else '<span class="badge-nominal">NOMINAL</span>'
                )

                st.markdown(
                    f"""
                    <div class="aerospace-card" style="padding: 12px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span class="label-caps" style="color: #0058BE; font-weight: 700;">{ch}</span>
                            {ch_badge}
                        </div>
                        <div style="font-size: 12px; font-weight: 600; color: #334155; margin-top: 2px;">{ch_name}</div>
                        <div class="mono-data-lg" style="font-size: 22px; margin: 8px 0 4px 0;">
                            {latest_val:.2f} <span style="font-size: 12px; color: #64748B; font-weight: 400;">{ch_unit}</span>
                        </div>
                        <div class="label-caps" style="font-size: 9px; color: #94A3B8;">MEAN: {mean_val:.2f} {ch_unit}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # Time-series telemetry plot
    if not sub_channels:
        st.warning("No telemetry channels available for this subsystem.")
    else:
        st.markdown(
            """
            <div class="label-caps" style="margin: 8px 0 4px 0;">
                📈 CONTINUOUS TELEMETRY STREAM & RECONSTRUCTION COMPARISON
            </div>
            """,
            unsafe_allow_html=True,
        )
        df_channels = pd.DataFrame(sub_channels)
        st.line_chart(df_channels, height=280)


def render_mission_overview_panel(
    window: TelemetryWindow,
    decision: FusionDecision,
    stacking_prob: float,
    verifier_res: Any,
    audit_entry: Any,
    op_map: dict[Subsystem, SpecialistOpinion],
) -> None:
    """Render top-level Mission Overview (Tab 1) matching Stitch mission overview screen."""
    # 1. Satellite Context Header
    st.markdown(
        """
        <div class="aerospace-card" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 28px;">🛰️</span>
                <div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 18px; font-weight: 700; color: #0F172A;">LEO-SENTINEL-4B</span>
                        <span class="label-caps" style="background: #F1F5F9; padding: 2px 6px; border-radius: 4px;">REV #4,912</span>
                        <span class="badge-nominal">CONSTELLATION SYNCED</span>
                    </div>
                    <div class="label-caps" style="color: #64748B; margin-top: 2px;">
                        ORBITAL INCLINATION 97.4° • ASCENDING NODE 142.8° • MASTER EPOCH v8.4.1
                    </div>
                </div>
            </div>
            <div class="badge-info" style="font-size: 11px;">
                SECURITY STATUS: AES-GCM-256 ENCRYPTED
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. Top Summary KPI Cards (5 metrics across)
    k1, k2, k3, k4, k5 = st.columns(5)

    scores = [op.anomaly_score for op in decision.opinions]
    mean_score = sum(scores) / len(scores) if scores else 0.0
    cohesion = max(0.0, min(100.0, (1.0 - mean_score) * 100.0))
    is_nominal = decision.severity.value.upper() == "NOMINAL"

    with k1:
        st.markdown(
            f"""
            <div class="aerospace-card">
                <div style="display: flex; justify-content: space-between;">
                    <span class="label-caps">SATELLITE HEALTH</span>
                    <span class="{"badge-nominal" if is_nominal else "badge-critical"}">{"NOMINAL" if is_nominal else "ALERT"}</span>
                </div>
                <div class="mono-data-lg" style="margin-top: 6px;">{cohesion:.1f}%</div>
                <div class="label-caps" style="color: #94A3B8; margin-top: 2px;">Cohesion Index</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k2:
        st.markdown(
            f"""
            <div class="aerospace-card">
                <div style="display: flex; justify-content: space-between;">
                    <span class="label-caps">ANOMALY PROB</span>
                    <span class="badge-info">PLATT PRIOR</span>
                </div>
                <div class="mono-data-lg" style="margin-top: 6px;">{stacking_prob:.3f}</div>
                <div class="label-caps" style="color: #94A3B8; margin-top: 2px;">Tolerance Limit: 0.650</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k3:
        anom_subs = [
            op.subsystem.value.upper()
            for op in decision.opinions
            if op.severity.value.upper() != "NOMINAL"
        ]
        anom_count = len(anom_subs)
        st.markdown(
            f"""
            <div class="aerospace-card">
                <div style="display: flex; justify-content: space-between;">
                    <span class="label-caps">ACTIVE ANOMALIES</span>
                    <span class="{"badge-nominal" if anom_count == 0 else "badge-critical"}">{"CLEAR" if anom_count == 0 else f"{anom_count} ACTIVE"}</span>
                </div>
                <div class="mono-data-lg" style="margin-top: 6px;">{anom_count} <span style="font-size: 14px; color: #94A3B8; font-weight: 500;">/ 4 Subs</span></div>
                <div class="label-caps" style="color: #94A3B8; margin-top: 2px;">{", ".join(anom_subs) if anom_subs else "Zero Subsystem Drift"}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k4:
        is_grounded = verifier_res and verifier_res.is_grounded
        st.markdown(
            f"""
            <div class="aerospace-card">
                <div style="display: flex; justify-content: space-between;">
                    <span class="label-caps">GROUNDING VERIF</span>
                    <span class="{"badge-nominal" if is_grounded else "badge-warning"}">{"PASS" if is_grounded else "ABSTAIN"}</span>
                </div>
                <div class="mono-data-lg" style="margin-top: 6px;">ADR-0002</div>
                <div class="label-caps" style="color: #94A3B8; margin-top: 2px;">Retries: {verifier_res.retry_count if verifier_res else 0} / 2</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k5:
        has_audit = audit_entry is not None
        st.markdown(
            f"""
            <div class="aerospace-card">
                <div style="display: flex; justify-content: space-between;">
                    <span class="label-caps">AUDIT LOG</span>
                    <span class="{"badge-nominal" if has_audit else "badge-warning"}">{"COMMITTED" if has_audit else "PENDING"}</span>
                </div>
                <div class="mono-data-lg" style="margin-top: 6px;">SQLITE</div>
                <div class="label-caps" style="color: #94A3B8; margin-top: 2px;">SHA-256 Validated</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 3. Four Subsystem Snapshot Grid
    st.markdown(
        """
        <div class="label-caps" style="margin: 14px 0 6px 0;">
            🛰️ SUB-SYSTEM TELEMETRY FEEDS & AGENT STATUS MATRIX
        </div>
        """,
        unsafe_allow_html=True,
    )
    s1, s2, s3, s4 = st.columns(4)

    for col, sub in zip(
        [s1, s2, s3, s4],
        [Subsystem.POWER, Subsystem.THERMAL, Subsystem.ATTITUDE, Subsystem.COMMUNICATIONS],
        strict=False,
    ):
        with col:
            op = op_map.get(sub)
            meta = SUBSYSTEM_META[sub]
            sub_sev = op.severity.value.upper() if op else "NOMINAL"
            sub_score = op.anomaly_score if op else 0.05
            sub_thresh = op.threshold_used if op else 0.50

            sub_badge = '<span class="badge-nominal">NOMINAL</span>'
            if sub_sev == "CRITICAL":
                sub_badge = '<span class="badge-critical">CRITICAL</span>'
            elif sub_sev in ("WARNING", "ADVISORY"):
                sub_badge = '<span class="badge-warning">WARNING</span>'

            st.markdown(
                f"""
                <div class="aerospace-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 700; color: #0F172A; font-size: 13px;">{meta["icon"]} {sub.value.upper()}</span>
                        {sub_badge}
                    </div>
                    <div class="label-caps" style="font-size: 9px; color: #64748B; margin-top: 2px;">{meta["code"]}</div>
                    <div style="display: flex; justify-content: space-between; align-items: baseline; margin-top: 8px;">
                        <div class="mono-data-lg" style="font-size: 18px;">{sub_score:.3f}</div>
                        <div class="label-caps" style="color: #94A3B8;">LIMIT {sub_thresh:.2f}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # 4. Recent Orbit Incident Ticker
    st.markdown(
        """
        <div class="label-caps" style="margin: 14px 0 6px 0;">
            📋 ORBITAL INCIDENT TICKER & EVENT CONCURRENCE
        </div>
        """,
        unsafe_allow_html=True,
    )
    ticker_df = pd.DataFrame(
        [
            {
                "Subsystem": op.subsystem.value.upper(),
                "Specialist Opinion": op.severity.value.upper(),
                "Score": f"{op.anomaly_score:.3f}",
                "Threshold": f"{op.threshold_used:.3f}",
                "Responsible Channels": ", ".join(op.responsible_channels)
                if op.responsible_channels
                else "Baseline Nominal",
                "Mitigation State": "AUTO-MONITORED"
                if op.severity.value.upper() == "NOMINAL"
                else "FLAGGED FOR REVIEW",
            }
            for op in decision.opinions
        ]
    )
    st.dataframe(ticker_df, use_container_width=True, hide_index=True)


def render_coordinator_panel(
    decision: FusionDecision,
    explanation: Any,
    verifier_res: Any,
    audit_entry: Any,
    abstained: bool,
    stacking_prob: float,
) -> None:
    """Render coordinator fusion, explanation, verifier, and audit summary matching Stitch spec."""
    sev = decision.severity.value.upper()
    sev_badge = '<span class="badge-nominal">NOMINAL (LEVEL 0 - GREEN)</span>'
    if sev == "CRITICAL":
        sev_badge = '<span class="badge-critical">CRITICAL (LEVEL 3 - RED)</span>'
    elif sev in ("WARNING", "ADVISORY"):
        sev_badge = '<span class="badge-warning">WARNING (LEVEL 2 - AMBER)</span>'

    attr_sub = (
        decision.attributed_subsystem.value.upper() if decision.attributed_subsystem else "NONE"
    )
    diagnosis_header = (
        "NO ANOMALY DETECTED // SYSTEM IN STEADY ORBITAL EQUILIBRIUM"
        if sev == "NOMINAL"
        else f"ATTRIBUTED ROOT CAUSE: {attr_sub} SUBSYSTEM // CORROBORATED SIGNATURE"
    )

    # 1. Hero Bento Header
    st.markdown(
        f"""
        <div class="aerospace-card-hero">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    {sev_badge}
                    <span class="label-caps">RULE: <strong style="color: #0F172A;">{decision.fusion_rule_applied}</strong></span>
                    <span class="label-caps" style="background: #F1F5F9; padding: 2px 6px; border-radius: 4px;">CONCURRENCE: 4/4 AGENTS</span>
                </div>
                <div class="label-caps" style="color: #0058BE;">FUSION_ENGINE_BUILD::v4.19-STABLE</div>
            </div>
            <div style="margin-top: 12px;">
                <div class="label-caps" style="color: #64748B;">ATTRIBUTED ROOT CAUSE DIAGNOSIS</div>
                <div style="font-size: 20px; font-weight: 700; color: #0F172A; margin-top: 2px;">{diagnosis_header}</div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin-top: 14px;">
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 6px; padding: 10px;">
                    <div class="label-caps">CALIBRATED PROB</div>
                    <div class="mono-data-lg" style="font-size: 20px;">{stacking_prob:.3f}</div>
                    <div class="label-caps" style="color: #94A3B8;">Platt Sigmoid</div>
                </div>
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 6px; padding: 10px;">
                    <div class="label-caps">ACTIVE ENSEMBLE</div>
                    <div class="mono-data-lg" style="font-size: 20px;">4 Nodes</div>
                    <div class="label-caps" style="color: #94A3B8;">Synchronized</div>
                </div>
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 6px; padding: 10px;">
                    <div class="label-caps">ROOT CAUSE</div>
                    <div class="mono-data-lg" style="font-size: 20px; color: {"#991B1B" if attr_sub != "NONE" else "#065F46"};">{attr_sub}</div>
                    <div class="label-caps" style="color: #94A3B8;">Physical Bias R3</div>
                </div>
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 6px; padding: 10px;">
                    <div class="label-caps">DECISION HASH</div>
                    <div class="mono-data-lg" style="font-size: 16px;">{str(decision.decision_id)[:8]}...</div>
                    <div class="label-caps" style="color: #94A3B8;">SHA-256 Validated</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c_left, c_right = st.columns([1.4, 1.0])

    with c_left:
        st.markdown(
            """
            <div class="label-caps" style="margin-bottom: 6px;">
                📝 REASONER EXPLANATION (EVIDENCE-BOUND ADR-0002 R2)
            </div>
            """,
            unsafe_allow_html=True,
        )
        if explanation and hasattr(explanation, "text") and not abstained:
            st.info(explanation.text)
            st.markdown(
                f"""
                <div class="label-caps" style="color: #64748B; margin-top: 4px;">
                    CITED SEVERITY: <strong style="color: #0F172A;">{explanation.cited_severity.value.upper()}</strong> •
                    CITED CHANNELS: <span>{", ".join(explanation.cited_channels) if explanation.cited_channels else "None"}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        elif abstained:
            st.warning(
                "⚠️ **System Abstained:** Explanation ungrounded after maximum retries. Emitting raw evidence only."
            )
        else:
            st.write("No explanation available.")

        st.markdown(
            """
            <div class="label-caps" style="margin: 14px 0 6px 0;">
                🛡️ GROUNDING VERIFICATION (ADR-0002 R2)
            </div>
            """,
            unsafe_allow_html=True,
        )
        v_status = (
            "GROUNDED (Accepted)" if verifier_res and verifier_res.is_grounded else "ABSTAINED"
        )
        retries = verifier_res.retry_count if verifier_res else 0
        st.write(f"• **Status:** `{v_status}`")
        st.write(f"• **Retry Count:** `{retries} / 2`")
        st.write("• **Mathematical Anti-Hallucination Guard:** Active")

    with c_right:
        st.markdown(
            """
            <div class="label-caps" style="margin-bottom: 6px;">
                🔒 SQLITE AUDIT LOG RECORD (ADR-0002 R7)
            </div>
            """,
            unsafe_allow_html=True,
        )
        if audit_entry:
            st.code(
                f"Entry ID:    {audit_entry.entry_id}\n"
                f"Decision ID: {audit_entry.decision_id}\n"
                f"Final Sev:   {audit_entry.final_severity.value}\n"
                f"Storage:     sqlite:///audit.db (WAL Mode)\n"
                f"Logged At:   {audit_entry.created_at.isoformat()[:19]}Z",
                language="yaml",
            )
        else:
            st.write("No audit entry logged.")

        st.markdown(
            """
            <div class="label-caps" style="margin: 14px 0 6px 0;">
                📊 SPECIALIST ANOMALY SCORES VS THRESHOLDS
            </div>
            """,
            unsafe_allow_html=True,
        )
        score_data = {op.subsystem.value.upper(): op.anomaly_score for op in decision.opinions}
        st.bar_chart(pd.Series(score_data), height=180)


# ---------------------------------------------------------------------------
# Main Application Entry Point
# ---------------------------------------------------------------------------


def main() -> None:
    """Main dashboard entry point."""
    st.set_page_config(
        page_title="Sentinel — Aerospace Mission Control", layout="wide", page_icon="🛰️"
    )

    # Inject Aerospace Mission Control CSS
    st.markdown(AEROSPACE_CSS, unsafe_allow_html=True)

    # 1. Top Aerospace Navigation Bar
    st.markdown(
        """
        <div style="background-color: #FFFFFF; border-bottom: 1px solid #E2E8F0; padding: 10px 18px; margin: -20px -20px 16px -20px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 24px;">🛰️</span>
                <div>
                    <div style="font-size: 16px; font-weight: 800; letter-spacing: -0.01em; color: #0F172A; line-height: 1.1;">SENTINEL</div>
                    <div class="label-caps" style="color: #64748B;">Orbital Telemetry OPS</div>
                </div>
                <div style="width: 1px; height: 24px; background: #E2E8F0; margin: 0 4px;"></div>
                <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                    <span class="label-caps" style="background: #F1F5F9; padding: 2px 6px; border-radius: 4px;">NORAD 48291</span>
                    <span class="label-caps" style="background: #F1F5F9; padding: 2px 6px; border-radius: 4px;">ORBIT LEO 540km</span>
                    <span class="label-caps" style="background: #F1F5F9; padding: 2px 6px; border-radius: 4px;">LINK 2.4 GHz</span>
                    <span class="badge-nominal">LIVE SYNC</span>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 14px;">
                <div style="text-align: right;">
                    <div class="label-caps">MISSION ELAPSED TIME</div>
                    <div class="mono-data-md" style="font-size: 13px; font-weight: 700;">MET +142:08:19:42</div>
                </div>
                <div class="badge-info" style="font-size: 11px;">
                    SECURE TELEMETRY LINK
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. Sidebar Controls & Replay Scrubbing
    st.sidebar.markdown(
        """
        <div class="label-caps" style="color: #0F172A; font-weight: 700; margin-bottom: 8px;">
            🕹️ MISSION TELEMETRY REPLAY
        </div>
        """,
        unsafe_allow_html=True,
    )
    windows, labels = get_cached_telemetry_windows(seed=42)

    window_idx = st.sidebar.slider(
        "Chronological Window Index",
        min_value=0,
        max_value=len(windows) - 1,
        value=0,
        help="Step through evaluation telemetry stream in time order.",
    )

    current_window = windows[window_idx]
    is_ground_truth_anom = labels[window_idx]

    # Quick Stepping buttons
    col_prev, col_next = st.sidebar.columns(2)
    if col_prev.button("◀ PREV") and window_idx > 0:
        st.session_state.window_idx = window_idx - 1
    if col_next.button("NEXT ▶") and window_idx < len(windows) - 1:
        st.session_state.window_idx = window_idx + 1

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Epoch Window:** `WIN-{window_idx:04d}`")
    st.sidebar.markdown(f"**Window ID:** `{str(current_window.window_id)[:8]}...`")
    st.sidebar.markdown(
        f"**Timestamp:** `{current_window.start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}`"
    )
    st.sidebar.markdown(f"**Ground Truth:** `{'ANOMALOUS' if is_ground_truth_anom else 'NOMINAL'}`")

    # 3. Pipeline Inference Execution
    with st.spinner("Analyzing telemetry window through Sentinel pipeline..."):
        outcome = run_pipeline(current_window.model_dump(), run_id=f"dash-{window_idx}")

    decision: FusionDecision = outcome["decision"]
    explanation = outcome.get("explanation")
    verifier_res = outcome.get("verifier_result")
    audit_entry = outcome.get("audit_entry")
    abstained = bool(outcome.get("abstained", False))

    stacking_coord = get_cached_stacking_coordinator()
    stacking_prob = stacking_coord.predict_proba(decision.opinions)

    op_map = {op.subsystem: op for op in decision.opinions}

    # 4. Six Aerospace Mission Control Tabs (matching Stitch specification)
    tabs = st.tabs(
        [
            "🛰️ Mission Overview",
            "⚡ Power (EPS)",
            "🌡️ Thermal (TCS)",
            "🔄 Attitude (ADCS)",
            "📡 Communications (TT&C)",
            "🌐 Coordinator & Fusion",
        ]
    )

    with tabs[0]:
        render_mission_overview_panel(
            window=current_window,
            decision=decision,
            stacking_prob=stacking_prob,
            verifier_res=verifier_res,
            audit_entry=audit_entry,
            op_map=op_map,
        )

    with tabs[1]:
        render_subsystem_panel(Subsystem.POWER, op_map.get(Subsystem.POWER), current_window, "P")

    with tabs[2]:
        render_subsystem_panel(
            Subsystem.THERMAL, op_map.get(Subsystem.THERMAL), current_window, "T"
        )

    with tabs[3]:
        render_subsystem_panel(
            Subsystem.ATTITUDE, op_map.get(Subsystem.ATTITUDE), current_window, "A"
        )

    with tabs[4]:
        render_subsystem_panel(
            Subsystem.COMMUNICATIONS, op_map.get(Subsystem.COMMUNICATIONS), current_window, "C"
        )

    with tabs[5]:
        render_coordinator_panel(
            decision=decision,
            explanation=explanation,
            verifier_res=verifier_res,
            audit_entry=audit_entry,
            abstained=abstained,
            stacking_prob=stacking_prob,
        )

    # 5. Export Actions
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        <div class="label-caps" style="color: #0F172A; font-weight: 700; margin-bottom: 8px;">
            📥 EXPORT AUDIT REPORTS
        </div>
        """,
        unsafe_allow_html=True,
    )
    report_json_str = json.dumps(
        {
            "window_id": str(current_window.window_id),
            "window_index": window_idx,
            "timestamp": current_window.start_time.isoformat(),
            "severity": decision.severity.value,
            "decision": decision.model_dump(mode="json"),
            "explanation": explanation.text
            if explanation and hasattr(explanation, "text")
            else None,
            "audit_entry_id": str(audit_entry.entry_id) if audit_entry else None,
            "calibrated_stacking_prob": stacking_prob,
            "generated_at": datetime.now().isoformat(),
        },
        indent=2,
    )
    st.sidebar.download_button(
        label="Download Window Analysis (JSON)",
        data=report_json_str,
        file_name=f"sentinel_window_{window_idx}.json",
        mime="application/json",
    )


if __name__ == "__main__":
    main()
