"""
Analysis Tools

This module contains analysis-related tools for LLM function calling.
"""

import logging
from typing import Dict, Any, List
import httpx
from ..registry import Tool, register_tool
from ...config import get_settings

logger = logging.getLogger(__name__)

@register_tool
class DependencyAnalysisTool(Tool):
    """Tool for analyzing dependencies between files"""
    
    @property
    def name(self) -> str:
        return "dependency_analysis"
    
    @property
    def description(self) -> str:
        return "Analyze dependencies between files"
    
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
    
    async def execute(self, paths: List[str]) -> Dict[str, Any]:
        """Execute dependency analysis using scanner service"""
        try:
            settings = get_settings()
            scanner_url = f"http://localhost:{settings.WEB_PORT}/scanner"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{scanner_url}/analyze-dependencies", json={
                    "paths": paths or ["/app/mock_enterprise"]
                })
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error in dependency analysis: {e}")
            return {"error": str(e), "dependencies": []}