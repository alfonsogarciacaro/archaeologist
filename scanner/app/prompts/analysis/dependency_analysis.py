"""
Analysis Prompts

This module contains prompts for different types of code analysis.
"""

class DependencyAnalysisPrompts:
    """Prompts for dependency analysis tasks"""
    
    SYSTEM_PROMPT = """Analyze dependencies between files in given paths.

Focus on identifying:
- Import dependencies between code files
- Database schema dependencies
- Shared data structures and identifiers
- Potential impact points

Provide clear evidence for each dependency relationship found."""
    
    USER_PROMPT_TEMPLATE = "Analyze dependencies in these paths: {paths}"

class ImpactAnalysisPrompts:
    """Prompts for impact analysis tasks"""
    
    SYSTEM_PROMPT = """Perform comprehensive impact analysis for given change.

Consider:
- Direct file references
- Dependency relationships
- Data flow implications
- External system integrations
- Potential knowledge gaps

Provide confidence scores and clear reasoning for your findings."""
    
    USER_PROMPT_TEMPLATE = "Analyze impact of this change: {query}"