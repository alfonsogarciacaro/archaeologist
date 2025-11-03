"""
Tools Module for Scanner Service

This module provides tools for LLM function calling,
including search, analysis, and external integrations.
"""

# Import existing vector DB tools
from .vector_db import VectorDatabaseInterface, Document, SearchResult
from .qdrant_adapter import QdrantAdapter
from .vector_db_factory import VectorDatabaseFactory, get_vector_db

# Import new LLM tools
try:
    from .registry import ToolRegistry, get_tool_registry, register_tool
    from .search import LiteralSearchTool, SemanticSearchTool
    from .analysis import DependencyAnalysisTool
    from .external import DatabaseQueryTool
    
    __all__ = [
        "VectorDatabaseInterface",
        "Document",
        "SearchResult",
        "QdrantAdapter",
        "VectorDatabaseFactory",
        "get_vector_db",
        "ToolRegistry",
        "get_tool_registry",
        "register_tool",
        "LiteralSearchTool",
        "SemanticSearchTool", 
        "DependencyAnalysisTool",
        "DatabaseQueryTool"
    ]
except ImportError:
    # New tool files not yet created - this is temporary
    __all__ = [
        "VectorDatabaseInterface",
        "Document",
        "SearchResult",
        "QdrantAdapter",
        "VectorDatabaseFactory",
        "get_vector_db"
    ]