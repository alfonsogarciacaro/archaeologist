"""
LLM Benchmarking Framework

This module provides comprehensive benchmarking capabilities for:
- Comparing different LLM providers (OpenAI, Anthropic, local models)
- Testing prompt effectiveness and variations
- Measuring tool combination performance
- Analyzing cost/performance trade-offs
"""

# Import benchmarking modules
from .models import (
    ModelConfig, 
    get_model_config, 
    get_all_model_configs,
    get_models_by_provider
)
from .prompts import (
    PromptVariant, 
    get_prompt_variant, 
    get_all_prompt_variants,
    get_prompt_variant_names
)
from .tools import (
    ToolCombination, 
    get_tool_combination, 
    get_all_tool_combinations,
    get_tool_combination_names,
    get_recommended_combination
)

__all__ = [
    # Models
    "ModelConfig",
    "get_model_config", 
    "get_all_model_configs",
    "get_models_by_provider",
    
    # Prompts
    "PromptVariant",
    "get_prompt_variant", 
    "get_all_prompt_variants",
    "get_prompt_variant_names",
    
    # Tools
    "ToolCombination", 
    "get_tool_combination", 
    "get_all_tool_combinations",
    "get_tool_combination_names",
    "get_recommended_combination"
]