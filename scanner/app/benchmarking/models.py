"""
Benchmarking Models Module

This module provides model-specific benchmarking configurations and utilities.
"""

from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class ModelConfig:
    """Configuration for a specific model"""
    provider: str
    model_name: str
    api_url: str
    api_key: str
    max_tokens: int
    temperature: float
    cost_per_1k_tokens: float

# Predefined model configurations
MODEL_CONFIGS = {
    "openai_gpt4": ModelConfig(
        provider="openai",
        model_name="gpt-4",
        api_url="https://api.openai.com/v1",
        api_key="your-openai-key",
        max_tokens=4000,
        temperature=0.1,
        cost_per_1k_tokens=0.03
    ),
    "openai_gpt35": ModelConfig(
        provider="openai",
        model_name="gpt-3.5-turbo",
        api_url="https://api.openai.com/v1",
        api_key="your-openai-key",
        max_tokens=4000,
        temperature=0.1,
        cost_per_1k_tokens=0.002
    ),
    "anthropic_claude3": ModelConfig(
        provider="anthropic",
        model_name="claude-3-sonnet-20240229",
        api_url="https://api.anthropic.com",
        api_key="your-anthropic-key",
        max_tokens=4000,
        temperature=0.1,
        cost_per_1k_tokens=0.015
    ),
    "ollama_llama2": ModelConfig(
        provider="ollama",
        model_name="llama2",
        api_url="http://localhost:11434",
        api_key="no-key-required",
        max_tokens=2000,
        temperature=0.1,
        cost_per_1k_tokens=0.0
    ),
    "mock_model": ModelConfig(
        provider="mock",
        model_name="mock",
        api_url="mock://localhost",
        api_key="mock-key",
        max_tokens=1000,
        temperature=0.0,
        cost_per_1k_tokens=0.0
    )
}

def get_model_config(model_key: str) -> ModelConfig:
    """Get model configuration by key"""
    if model_key not in MODEL_CONFIGS:
        raise ValueError(f"Unknown model configuration: {model_key}")
    return MODEL_CONFIGS[model_key]

def get_all_model_configs() -> Dict[str, ModelConfig]:
    """Get all model configurations"""
    return MODEL_CONFIGS.copy()

def get_models_by_provider(provider: str) -> List[str]:
    """Get all model keys for a specific provider"""
    return [
        key for key, config in MODEL_CONFIGS.items() 
        if config.provider == provider
    ]