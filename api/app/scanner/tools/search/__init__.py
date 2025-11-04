"""
Search Tools

This module contains search-related tools for LLM function calling.
"""

import logging
from typing import Dict, Any, List
import httpx
from ..registry import Tool, register_tool
from ...config import get_settings

logger = logging.getLogger(__name__)

@register_tool
class LiteralSearchTool(Tool):
    """Tool for exact string matching in code"""
    
    @property
    def name(self) -> str:
        return "literal_search"
    
    @property
    def description(self) -> str:
        return "Search for exact string matches in code"
    
    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
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
    
    async def execute(self, query: str, paths: List[str] = None) -> Dict[str, Any]:
        """Execute literal search using scanner service"""
        try:
            settings = get_settings()
            scanner_url = f"http://localhost:{settings.WEB_PORT}/scanner"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{scanner_url}/scan", json={
                    "query": query,
                    "paths": paths or ["/app/mock_enterprise"]
                })
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error in literal search: {e}")
            return {"error": str(e), "results": []}

@register_tool
class SemanticSearchTool(Tool):
    """Tool for semantic code search"""
    
    @property
    def name(self) -> str:
        return "semantic_search"
    
    @property
    def description(self) -> str:
        return "Search for semantically related code"
    
    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
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
    
    async def execute(self, concept: str, limit: int = 10) -> Dict[str, Any]:
        """Execute semantic search using scanner's RAG service"""
        try:
            settings = get_settings()
            scanner_url = f"http://localhost:{settings.WEB_PORT}/scanner"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{scanner_url}/search", json={
                    "query": concept,
                    "limit": limit
                })
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return {"error": str(e), "results": []}