"""
Tool Descriptions

This module contains JSON schemas and descriptions for LLM tools.
"""

class ToolDescriptions:
    """JSON schemas for LLM function calling tools"""
    
    LITERAL_SEARCH = {
        "type": "function",
        "function": {
            "name": "literal_search",
            "description": "Search for exact string matches in code",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Exact string to search for"
                    },
                    "paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Paths to search in"
                    }
                },
                "required": ["query"]
            }
        }
    }
    
    DEPENDENCY_ANALYSIS = {
        "type": "function", 
        "function": {
            "name": "dependency_analysis",
            "description": "Analyze dependencies between files",
            "parameters": {
                "type": "object",
                "properties": {
                    "paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Paths to analyze"
                    }
                },
                "required": ["paths"]
            }
        }
    }
    
    SEMANTIC_SEARCH = {
        "type": "function",
        "function": {
            "name": "semantic_search",
            "description": "Search for semantically related code",
            "parameters": {
                "type": "object",
                "properties": {
                    "concept": {
                        "type": "string",
                        "description": "Concept to search for"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results to return"
                    }
                },
                "required": ["concept"]
            }
        }
    }
    
    @classmethod
    def get_all_tools(cls) -> list:
        """Get all available tool descriptions"""
        return [
            cls.LITERAL_SEARCH,
            cls.DEPENDENCY_ANALYSIS,
            cls.SEMANTIC_SEARCH
        ]
    
    @classmethod
    def get_tool_by_name(cls, name: str) -> dict:
        """Get tool description by name"""
        tools = {
            "literal_search": cls.LITERAL_SEARCH,
            "dependency_analysis": cls.DEPENDENCY_ANALYSIS,
            "semantic_search": cls.SEMANTIC_SEARCH
        }
        return tools.get(name, {})