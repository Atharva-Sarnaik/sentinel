"""
services.fusion.corroboration
================================
Cross-subsystem corroboration rules (config-driven).

Rules are loaded from corroboration_rules.yaml (or embedded defaults).
Evaluates co-occurring anomalies across subsystems to detect multi-subsystem
couplings and cascading spacecraft anomalies (task T2.2).

Design rule (ADR-0002):
  • Deterministic: Same input opinions always trigger the exact same rule.
  • No LLM involvement in rule evaluation.

Owner:   Atharva Sarnaik (@Atharva-Sarnaik)
Tier:    2 (task T2.2)
Status:  complete — config-driven cross-subsystem corroboration rule engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from libs.contracts import Severity, SpecialistOpinion, Subsystem

DEFAULT_RULES_PATH = Path("libs/config/corroboration_rules.yaml")


@dataclass(frozen=True)
class CorroborationRule:
    """Parsed corroboration rule definition."""

    id: str
    name: str
    description: str
    required_subsystems: frozenset[Subsystem]
    min_anomalous: int | None
    max_anomalous: int | None
    escalate_to: Severity | None
    primary_bias: Subsystem | None


def _parse_severity(val: str | None) -> Severity | None:
    if val is None:
        return None
    try:
        return Severity(val.lower())
    except ValueError:
        return None


def _parse_subsystem(val: str | None) -> Subsystem | None:
    if val is None:
        return None
    try:
        return Subsystem(val.lower())
    except ValueError:
        return None


def load_corroboration_rules(
    rules_path: Path | str = DEFAULT_RULES_PATH,
) -> list[CorroborationRule]:
    """
    Load and parse corroboration rules from YAML.
    Falls back to built-in hardcoded rules if the file is missing.
    """
    path = Path(rules_path)
    raw_rules: list[dict[str, Any]] = []

    if path.is_file():
        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict) and "rules" in data:
                    raw_rules = data["rules"]
        except Exception:
            raw_rules = []

    if not raw_rules:
        # Fallback default rules
        raw_rules = [
            {
                "id": "RULE_CASCADE_001",
                "name": "cascading_system_failure",
                "description": "Three or more subsystems reporting anomalies indicate systemic failure.",
                "min_anomalous_subsystems": 3,
                "escalate_to": "critical",
            },
            {
                "id": "RULE_PWR_THM_002",
                "name": "power_thermal_coupling",
                "description": "Co-occurring power and thermal anomalies indicate battery thermal runaway or panel overheat.",
                "required_subsystems": ["power", "thermal"],
                "escalate_to": "critical",
                "primary_bias": "power",
            },
            {
                "id": "RULE_ATT_PWR_003",
                "name": "attitude_power_coupling",
                "description": "Attitude tumble causing loss of sun-pointing and solar array power drop.",
                "required_subsystems": ["attitude", "power"],
                "escalate_to": "critical",
                "primary_bias": "attitude",
            },
            {
                "id": "RULE_ATT_COM_004",
                "name": "attitude_comms_coupling",
                "description": "Attitude pointing error causing antenna misalignment and downlink signal loss.",
                "required_subsystems": ["attitude", "communications"],
                "escalate_to": "warning",
                "primary_bias": "attitude",
            },
            {
                "id": "RULE_SINGLE_ISO_005",
                "name": "single_subsystem_isolated",
                "description": "Single subsystem anomaly without cross-subsystem corroboration.",
                "min_anomalous_subsystems": 1,
                "max_anomalous_subsystems": 1,
                "escalate_to": None,
            },
            {
                "id": "RULE_NOMINAL_000",
                "name": "nominal_baseline",
                "description": "All subsystems are within nominal operating limits.",
                "min_anomalous_subsystems": 0,
                "max_anomalous_subsystems": 0,
                "escalate_to": "nominal",
            },
        ]

    rules: list[CorroborationRule] = []
    for r in raw_rules:
        req_subs = frozenset(
            Subsystem(s.lower()) for s in r.get("required_subsystems", []) if _parse_subsystem(s)
        )
        rules.append(
            CorroborationRule(
                id=r.get("id", "UNKNOWN"),
                name=r.get("name", "unknown_rule"),
                description=r.get("description", ""),
                required_subsystems=req_subs,
                min_anomalous=r.get("min_anomalous_subsystems"),
                max_anomalous=r.get("max_anomalous_subsystems"),
                escalate_to=_parse_severity(r.get("escalate_to")),
                primary_bias=_parse_subsystem(r.get("primary_bias")),
            )
        )

    return rules


@dataclass(frozen=True)
class CorroborationEvaluation:
    """Full evaluation result from corroboration matching."""

    corroborating_subsystems: list[Subsystem]
    rule_name: str
    escalate_to: Severity | None
    primary_bias: Subsystem | None


def evaluate_corroboration_detailed(
    opinions: list[SpecialistOpinion],
    rules: list[CorroborationRule] | None = None,
) -> CorroborationEvaluation:
    """
    Perform detailed corroboration rule evaluation.
    """
    active_rules = rules if rules is not None else load_corroboration_rules()

    # Identify anomalous subsystems
    anomalous_subs = sorted(
        {op.subsystem for op in opinions if op.is_anomalous},
        key=lambda s: s.value,
    )
    n_anomalous = len(anomalous_subs)
    anom_set = frozenset(anomalous_subs)

    # 1. Check cascading multi-subsystem failure (>= 3 anomalous subsystems)
    for rule in active_rules:
        if (
            rule.min_anomalous is not None
            and rule.min_anomalous >= 3
            and n_anomalous >= rule.min_anomalous
        ):
            return CorroborationEvaluation(
                corroborating_subsystems=anomalous_subs,
                rule_name=rule.name,
                escalate_to=rule.escalate_to,
                primary_bias=rule.primary_bias,
            )

    # 2. Check specific paired subsystem couplings (e.g. Power + Thermal, Attitude + Power)
    for rule in active_rules:
        if rule.required_subsystems and rule.required_subsystems.issubset(anom_set):
            return CorroborationEvaluation(
                corroborating_subsystems=anomalous_subs,
                rule_name=rule.name,
                escalate_to=rule.escalate_to,
                primary_bias=rule.primary_bias,
            )

    # 3. Check single isolated anomaly
    if n_anomalous == 1:
        for rule in active_rules:
            if rule.min_anomalous == 1 and rule.max_anomalous == 1:
                return CorroborationEvaluation(
                    corroborating_subsystems=[],
                    rule_name=rule.name,
                    escalate_to=rule.escalate_to,
                    primary_bias=anomalous_subs[0],
                )

    # 4. Check nominal baseline
    if n_anomalous == 0:
        for rule in active_rules:
            if rule.min_anomalous == 0 and rule.max_anomalous == 0:
                return CorroborationEvaluation(
                    corroborating_subsystems=[],
                    rule_name=rule.name,
                    escalate_to=rule.escalate_to,
                    primary_bias=None,
                )

    # Default fallback if 2 anomalous subsystems didn't match specific coupling
    return CorroborationEvaluation(
        corroborating_subsystems=anomalous_subs,
        rule_name="generic_multi_subsystem_anomaly",
        escalate_to=Severity.WARNING,
        primary_bias=anomalous_subs[0] if anomalous_subs else None,
    )


def evaluate_corroboration(
    opinions: list[SpecialistOpinion],
) -> tuple[list[Subsystem], str]:
    """
    Evaluate cross-subsystem corroboration rules.

    Returns:
        (corroborating_subsystems, rule_label_applied)
    """
    evaluation = evaluate_corroboration_detailed(opinions)
    return evaluation.corroborating_subsystems, evaluation.rule_name
