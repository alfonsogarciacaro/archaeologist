"""
LLM Module for Scanner Service

This module provides LLM capabilities for code investigation and analysis,
including provider interfaces, mock services, and integration with scanner tools.
"""

# Import will be available after files are created
try:
    from .llm_interface import LLMProvider, get_llm_provider
    from .mock_llm import MockLLMService, get_mock_llm_service
    
    __all__ = [
        "LLMProvider",
        "get_llm_provider", 
        "MockLLMService",
        "get_mock_llm_service"
    ]
except ImportError:
    # Files not yet created - this is temporary
    __all__ = []