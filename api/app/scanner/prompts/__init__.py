"""
Prompts Module for Scanner Service

This module provides systematic prompt management for LLM interactions,
including investigation prompts, analysis prompts, and reusable templates.
"""

# Import will be available after files are created
try:
    from .investigation.system_prompts import InvestigationPrompts
    from .analysis.dependency_analysis import DependencyAnalysisPrompts
    from .analysis.impact_analysis import ImpactAnalysisPrompts
    from .templates.tool_descriptions import ToolDescriptions
    
    __all__ = [
        "InvestigationPrompts",
        "DependencyAnalysisPrompts", 
        "ImpactAnalysisPrompts",
        "ToolDescriptions"
    ]
except ImportError:
    # Files not yet created - this is temporary
    __all__ = []