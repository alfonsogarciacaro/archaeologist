"""
Impact Analysis Prompts

This module contains prompts for impact analysis tasks.
"""

class ImpactAnalysisPrompts:
    """Prompts for impact analysis tasks"""
    
    SYSTEM_PROMPT = """Perform comprehensive impact analysis for the given change.

Consider:
- Direct file references
- Dependency relationships
- Data flow implications
- External system integrations
- Potential knowledge gaps

Provide confidence scores and clear reasoning for your findings."""
    
    USER_PROMPT_TEMPLATE = "Analyze impact of this change: {query}"