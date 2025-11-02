"""
LLM Interface for Enterprise Code Archaeologist

This module provides a flexible interface for LLM services that can work with:
- Local models (llamacpp, Ollama)
- Online models (OpenAI, Anthropic, etc.)
- Mock LLM for testing
"""

import logging
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import httpx
from .config import get_settings

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    async def investigate_change(self, query: str) -> Dict[str, Any]:
        """Investigate a change using the LLM"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check if the LLM service is healthy"""
        pass

class OpenAIProvider(LLMProvider):
    """OpenAI-compatible API provider"""
    
    def __init__(self):
        self.api_url = get_settings().LLM_API_URL or "http://localhost:11434/v1"
        self.api_key = get_settings().LLM_API_KEY or "no-key-required"
        self.model = get_settings().LLM_MODEL or "llama2"
        self.client = httpx.AsyncClient(base_url=self.api_url, timeout=60.0)
    
    async def investigate_change(self, query: str) -> Dict[str, Any]:
        """Use OpenAI-compatible API for investigation"""
        
        # Define tools available to LLM
        tools = [
            {
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
            },
            {
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
            },
            {
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
        ]
        
        # System prompt
        system_prompt = """You are an expert software architect investigating code changes in enterprise systems.

Your task is to analyze the impact of proposed changes by:
1. Finding exact matches using literal_search
2. Analyzing dependencies using dependency_analysis  
3. Discovering related code using semantic_search
4. Synthesizing findings into a comprehensive impact report

You must:
- Use the provided tools to gather evidence
- Be thorough in your analysis
- Identify potential knowledge gaps
- Provide clear reasoning for your conclusions
- Include confidence scores for your findings

Focus on understanding how changes propagate through the system and what might break."""
        
        try:
            headers={
                "Content-Type": "application/json"
            }
            if self.api_key != "no-key-required":
                headers["Authorization"] = f"Bearer {self.api_key}"

            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Investigate this change: {query}"}
                    ],
                    "tools": tools,
                    "tool_choice": "auto"
                },
                headers=headers
            )
            
            result = response.json()
            
            # Handle tool calls
            if "choices" in result and len(result["choices"]) > 0:
                message = result["choices"][0]["message"]
                
                if "tool_calls" in message:
                    # Execute tool calls and get results
                    tool_results = await self._execute_tool_calls(message["tool_calls"])
                    
                    # Send results back to LLM for synthesis
                    synthesis_response = await self.client.post(
                        "/chat/completions",
                        json={
                            "model": self.model,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": f"Investigate this change: {query}"},
                                message,
                                {"role": "tool", "content": "Tool results: " + str(tool_results)}
                            ]
                        }
                    )
                    
                    return self._parse_llm_response(synthesis_response.json())
                else:
                    return self._parse_llm_response(result)
            
            return {"error": "No response from LLM", "details": result}
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return {
                "error": f"LLM API error: {str(e)}",
                "nodes": [],
                "edges": [],
                "knowledge_gaps": [],
                "explanation": {
                    "reasoning_steps": [f"Error occurred: {str(e)}"],
                    "evidence_sources": [],
                    "confidence_score": 0.0
                }
            }
    
    async def _execute_tool_calls(self, tool_calls: List[Dict]) -> Dict[str, Any]:
        """Execute tool calls and return results"""
        results = {}
        
        for tool_call in tool_calls:
            function_name = tool_call["function"]["name"]
            arguments = tool_call["function"]["arguments"]
            
            if function_name == "literal_search":
                results = await self._literal_search(arguments.get("query"), arguments.get("paths", []))
                results["literal_search"] = results
            elif function_name == "dependency_analysis":
                results["dependency_analysis"] = await self._dependency_analysis(arguments.get("paths", []))
            elif function_name == "semantic_search":
                results["semantic_search"] = await self._semantic_search(arguments.get("concept"), arguments.get("limit", 10))
        
        return results
    
    async def _literal_search(self, query: str, paths: List[str]) -> Dict[str, Any]:
        """Execute literal search using scanner service"""
        try:
            scanner_url = get_settings().SCANNER_URL or "http://scanner:8000"
            async with httpx.AsyncClient() as client:
                response = await client.post("/scan", json={
                    "query": query,
                    "paths": paths
                })
                return response.json()
        except Exception as e:
            logger.error(f"Error in literal search: {e}")
            return {"error": str(e), "results": []}
    
    async def _dependency_analysis(self, paths: List[str]) -> Dict[str, Any]:
        """Execute dependency analysis using scanner service"""
        try:
            scanner_url = get_settings().SCANNER_URL or "http://scanner:8000"
            async with httpx.AsyncClient() as client:
                response = await client.post("/analyze-dependencies", json={
                    "paths": paths
                })
                return response.json()
        except Exception as e:
            logger.error(f"Error in dependency analysis: {e}")
            return {"error": str(e), "dependencies": []}
    
    async def _semantic_search(self, concept: str, limit: int) -> Dict[str, Any]:
        """Execute semantic search (placeholder for now)"""
        # For prototype, return mock semantic results
        return {
            "results": [
                {
                    "file": f"mock_file_related_to_{concept}.py",
                    "relevance": 0.8,
                    "explanation": f"Semantically related to {concept}"
                }
            ]
        }
    
    def _parse_llm_response(self, response: Dict) -> Dict[str, Any]:
        """Parse LLM response into our format"""
        if "choices" not in response or len(response["choices"]) == 0:
            return {"error": "No choices in response", "details": response}
        
        message = response["choices"][0]["message"]
        content = message.get("content", "")
        
        # Try to parse as JSON
        import json
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # If not JSON, return as explanation
            return {
                "nodes": [],
                "edges": [],
                "knowledge_gaps": [],
                "explanation": {
                    "reasoning_steps": [content],
                    "evidence_sources": [],
                    "confidence_score": 0.5
                }
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if OpenAI API is healthy"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("/models", timeout=5.0)
                return {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "api_url": self.api_url,
                    "model": self.model
                }
        except Exception as e:
            return {
                "status": f"unhealthy: {str(e)}",
                "api_url": self.api_url,
                "model": self.model
            }

class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing"""
    
    def __init__(self):
        from .mock_llm import get_mock_llm_service
        self.mock_service = None
    
    async def _get_service(self):
        if self.mock_service is None:
            from .mock_llm import get_mock_llm_service
            self.mock_service = await get_mock_llm_service()
        return self.mock_service
    
    async def investigate_change(self, query: str) -> Dict[str, Any]:
        """Use mock LLM service for investigation"""
        service = await self._get_service()
        return await service.investigate_change(query)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if mock LLM is healthy"""
        return {
            "status": "healthy",
            "provider": "mock",
            "note": "Mock LLM service for testing"
        }

class LLMFactory:
    """Factory for creating LLM providers"""
    
    @staticmethod
    async def create_provider() -> LLMProvider:
        """Create LLM provider based on configuration"""
        provider_type = get_settings().LLM_PROVIDER or "mock"
        
        if provider_type.lower() == "mock":
            return MockLLMProvider()
        elif provider_type.lower() in ["openai", "ollama", "llamacpp"]:
            return OpenAIProvider()
        else:
            logger.warning(f"Unknown LLM provider: {provider_type}, falling back to mock")
            return MockLLMProvider()

# Singleton instance for easy access
_llm_provider: Optional[LLMProvider] = None

async def get_llm_provider() -> LLMProvider:
    """Get the LLM provider instance"""
    global _llm_provider
    if _llm_provider is None:
        _llm_provider = await LLMFactory.create_provider()
    return _llm_provider