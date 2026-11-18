"""services.fusion package."""

from services.fusion.attribution import attribute_subsystem
from services.fusion.corroboration import (
    CorroborationRule,
    evaluate_corroboration,
    evaluate_corroboration_detailed,
    load_corroboration_rules,
)
from services.fusion.engine import fuse
from services.fusion.stacking import (
    LearnedStackingCoordinator,
    compare_stacking_vs_rules,
    compute_expected_calibration_error,
    extract_opinion_features,
)

__all__ = [
    "CorroborationRule",
    "LearnedStackingCoordinator",
    "attribute_subsystem",
    "compare_stacking_vs_rules",
    "compute_expected_calibration_error",
    "evaluate_corroboration",
    "evaluate_corroboration_detailed",
    "extract_opinion_features",
    "fuse",
    "load_corroboration_rules",
]
