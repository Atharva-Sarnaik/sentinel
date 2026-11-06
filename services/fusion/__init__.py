"""services.fusion package."""

from services.fusion.attribution import attribute_subsystem
from services.fusion.corroboration import (
    CorroborationRule,
    evaluate_corroboration,
    evaluate_corroboration_detailed,
    load_corroboration_rules,
)
from services.fusion.engine import fuse

__all__ = [
    "fuse",
    "evaluate_corroboration",
    "evaluate_corroboration_detailed",
    "load_corroboration_rules",
    "CorroborationRule",
    "attribute_subsystem",
]
