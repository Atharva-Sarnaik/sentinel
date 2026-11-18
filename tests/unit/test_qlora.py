"""
tests.unit.test_qlora
=====================
Unit tests for Task T6.3: QLoRA Fine-Tuning and Local Explanation Model (services.reasoner.qlora).

Tests:
  - QLoRAConfig configuration integrity and VRAM budget.
  - Instruction prompt formatting and evidence bounding.
  - Local QLoRA explanation generation conforming to Explanation contract.
  - Comparative analysis of Local QLoRA vs Cloud API across quality, latency, cost, and security.

Owner:   Atharva Sarnaik (@Atharva-Sarnaik) / Sujal Hede (@Sujalhede)
Tier:    6 (task T6.3)
"""

from __future__ import annotations

import uuid

from libs.common.helpers import utc_now
from libs.contracts import Explanation, FusionDecision, Severity, SpecialistOpinion, Subsystem
from services.reasoner.qlora import (
    LocalQLoRAExplanationEngine,
    QLoRAConfig,
    compare_qlora_vs_api,
    format_instruction_prompt,
)


def _make_dummy_decision() -> FusionDecision:
    """Helper to create a valid FusionDecision for testing."""
    w_id = uuid.uuid4()
    op = SpecialistOpinion(
        window_id=w_id,
        subsystem=Subsystem.POWER,
        anomaly_score=0.88,
        severity=Severity.CRITICAL,
        responsible_channels=["P-1", "P-2"],
        threshold_used=0.50,
        model_run_id="power-test",
        created_at=utc_now(),
    )
    return FusionDecision(
        window_id=w_id,
        opinions=[op],
        severity=Severity.CRITICAL,
        corroborating_subsystems=[Subsystem.POWER],
        attributed_subsystem=Subsystem.POWER,
        fusion_rule_applied="single_subsystem_critical",
        created_at=utc_now(),
    )


def test_qlora_config() -> None:
    """Verify QLoRAConfig specifies 4-bit quantization within the RTX 4050 VRAM budget."""
    cfg = QLoRAConfig()
    assert cfg.load_in_4bit is True
    assert cfg.bnb_4bit_quant_type == "nf4"
    assert cfg.lora_r == 8
    assert cfg.lora_alpha == 16
    assert cfg.vram_budget_gb <= 4.0  # Must fit within 6GB laptop GPU

    d = cfg.to_dict()
    assert isinstance(d, dict)
    assert d["base_model_id"] == "Qwen/Qwen2.5-0.5B-Instruct"


def test_format_instruction_prompt() -> None:
    """Verify instruction prompt binds strictly to evidence channels and severity."""
    dec = _make_dummy_decision()
    formatted = format_instruction_prompt(dec)

    assert "instruction" in formatted
    assert "response" in formatted
    assert "full_text" in formatted

    instr = formatted["instruction"]
    assert "P-1" in instr
    assert "P-2" in instr
    assert "POWER" in instr
    assert "CRITICAL" in instr

    resp = formatted["response"]
    assert "power" in resp.lower()
    assert "critical" in resp.lower()
    assert "P-1" in resp


def test_local_qlora_engine_execution() -> None:
    """Verify LocalQLoRAExplanationEngine generates a valid Explanation object."""
    engine = LocalQLoRAExplanationEngine()
    dec = _make_dummy_decision()

    expl, meta = engine.generate_explanation(dec)
    assert isinstance(expl, Explanation)
    assert expl.decision_id == dec.decision_id
    assert "power" in expl.text.lower()
    assert "critical" in expl.text.lower()
    assert expl.llm_model == "sentinel-qwen-0.5b-qlora"

    assert meta["air_gap_capable"] is True
    assert meta["estimated_cost_usd"] == 0.0
    assert meta["vram_used_mb"] > 0
    assert meta["latency_ms"] >= 0.0


def test_compare_qlora_vs_api() -> None:
    """Verify comparison between Local QLoRA and Cloud API across quality, latency, and cost."""
    decisions = [_make_dummy_decision(), _make_dummy_decision()]
    comp = compare_qlora_vs_api(decisions)

    assert "cloud_api" in comp
    assert "local_qlora" in comp
    assert "recommendation" in comp

    api_data = comp["cloud_api"]
    qlora_data = comp["local_qlora"]

    # Latency: Local QLoRA should have much lower latency
    assert qlora_data["mean_latency_ms"] < api_data["mean_latency_ms"]
    assert qlora_data["speedup_factor"] > 1.0

    # Cost: Local QLoRA should be 0 USD, API > 0 USD
    assert qlora_data["cost_per_1k_queries_usd"] == 0.0
    assert api_data["cost_per_1k_queries_usd"] > 0.0

    # Security: Local QLoRA is air-gap capable, API requires outbound internet
    assert "CAPABLE" in qlora_data["air_gap_flight_operations"]
    assert "NOT CAPABLE" in api_data["air_gap_flight_operations"]
