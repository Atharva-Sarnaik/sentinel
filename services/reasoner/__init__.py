"""services.reasoner package."""

from services.reasoner.qlora import (
    LocalQLoRAExplanationEngine,
    QLoRAConfig,
    compare_qlora_vs_api,
    format_instruction_prompt,
)
from services.reasoner.reasoner import (
    DEFAULT_OPENAI_MODEL,
    DEFAULT_PROMPT_VERSION,
    generate_explanation,
    generate_explanation_with_metadata,
    get_openai_config,
    load_prompt_template,
    mock_generate_explanation,
    openai_generate_explanation,
)
from services.reasoner.schemas import (
    EXPLANATION_JSON_SCHEMA,
    ReasonerExecutionMetadata,
    ReasonerOutputSchema,
)

__all__ = [
    "DEFAULT_OPENAI_MODEL",
    "DEFAULT_PROMPT_VERSION",
    "EXPLANATION_JSON_SCHEMA",
    "LocalQLoRAExplanationEngine",
    "QLoRAConfig",
    "ReasonerExecutionMetadata",
    "ReasonerOutputSchema",
    "compare_qlora_vs_api",
    "format_instruction_prompt",
    "generate_explanation",
    "generate_explanation_with_metadata",
    "get_openai_config",
    "load_prompt_template",
    "mock_generate_explanation",
    "openai_generate_explanation",
]
