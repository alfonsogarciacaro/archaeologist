"""
Benchmarking Tools Module

This module provides tool combination configurations for testing different tool strategies.
"""

from typing import Dict, List, Set
from dataclasses import dataclass

@dataclass
class ToolCombination:
    """A specific combination of tools for testing"""
    name: str
    tools: List[str]
    description: str
    expected_use_case: str

# All available tools
ALL_AVAILABLE_TOOLS = [
    "literal_search",
    "semantic_search", 
    "dependency_analysis",
    "impact_analysis",
    "file_content_analysis",
    "api_endpoint_analysis"
]

# All tools enabled (maximum capability)
ALL_TOOLS = ToolCombination(
    name="all",
    tools=ALL_AVAILABLE_TOOLS,
    description="All available tools enabled for comprehensive analysis",
    expected_use_case="Complex enterprise changes requiring thorough investigation"
)

# Search only tools (minimal approach)
SEARCH_ONLY = ToolCombination(
    name="search_only",
    tools=["literal_search", "semantic_search"],
    description="Only search tools enabled for basic investigation",
    expected_use_case="Simple changes with minimal dependencies"
)

# Analysis only tools (deep dive)
ANALYSIS_ONLY = ToolCombination(
    name="analysis_only", 
    tools=["dependency_analysis", "impact_analysis"],
    description="Only analysis tools enabled for deep dependency investigation",
    expected_use_case="Architecture changes and refactoring efforts"
)

# Search + Analysis (balanced approach)
SEARCH_ANALYSIS = ToolCombination(
    name="search_analysis",
    tools=["literal_search", "semantic_search", "dependency_analysis", "impact_analysis"],
    description="Search and analysis tools for balanced investigation",
    expected_use_case="Most standard changes requiring good coverage"
)

# Minimal tools (fastest)
MINIMAL = ToolCombination(
    name="minimal",
    tools=["literal_search"],
    description="Only literal search for fastest basic investigation",
    expected_use_case="Quick assessments and time-critical situations"
)

# Semantic focused (AI-powered)
SEMANTIC_FOCUSED = ToolCombination(
    name="semantic_focused",
    tools=["semantic_search", "impact_analysis"],
    description="Semantic search with impact analysis for intelligent investigation",
    expected_use_case="Changes requiring understanding of code context and meaning"
)

# Dependency focused (architecture)
DEPENDENCY_FOCUSED = ToolCombination(
    name="dependency_focused",
    tools=["literal_search", "dependency_analysis", "file_content_analysis"],
    description="Tools focused on understanding code dependencies",
    expected_use_case="Refactoring, service decomposition, architecture changes"
)

# API focused (service changes)
API_FOCUSED = ToolCombination(
    name="api_focused",
    tools=["semantic_search", "api_endpoint_analysis", "impact_analysis"],
    description="Tools focused on API and service changes",
    expected_use_case="API modifications, service integrations, contract changes"
)

# All tool combinations
TOOL_COMBINATIONS = {
    "all": ALL_TOOLS,
    "search_only": SEARCH_ONLY,
    "analysis_only": ANALYSIS_ONLY,
    "search_analysis": SEARCH_ANALYSIS,
    "minimal": MINIMAL,
    "semantic_focused": SEMANTIC_FOCUSED,
    "dependency_focused": DEPENDENCY_FOCUSED,
    "api_focused": API_FOCUSED
}

def get_tool_combination(name: str) -> ToolCombination:
    """Get tool combination by name"""
    if name not in TOOL_COMBINATIONS:
        raise ValueError(f"Unknown tool combination: {name}")
    return TOOL_COMBINATIONS[name]

def get_all_tool_combinations() -> Dict[str, ToolCombination]:
    """Get all tool combinations"""
    return TOOL_COMBINATIONS.copy()

def get_tool_combination_names() -> List[str]:
    """Get all tool combination names"""
    return list(TOOL_COMBINATIONS.keys())

def get_tools_for_combination(name: str) -> List[str]:
    """Get tool list for specific combination"""
    combination = get_tool_combination(name)
    return combination.tools

def validate_tool_combination(tools: List[str]) -> bool:
    """Validate that all tools in combination are available"""
    tool_set = set(tools)
    available_set = set(ALL_AVAILABLE_TOOLS)
    return tool_set.issubset(available_set)

def get_recommended_combination(change_type: str) -> str:
    """Get recommended tool combination for change type"""
    recommendations = {
        "api_change": "api_focused",
        "refactoring": "dependency_focused", 
        "new_feature": "search_analysis",
        "bug_fix": "search_only",
        "architecture": "all",
        "performance": "analysis_only",
        "security": "semantic_focused",
        "database": "dependency_focused",
        "ui_change": "minimal",
        "config_change": "search_only"
    }
    
    return recommendations.get(change_type.lower(), "search_analysis")