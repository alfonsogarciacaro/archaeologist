"""
LLM Interface for Scanner Service

This module provides a flexible interface for LLM services that can work with:
- Local models (llamacpp, Ollama)
- Online models (OpenAI, Anthropic, etc.)
- Mock LLM for testing
"""

import logging
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import httpx
from ..config import get_settings
from ..prompts.investigation.system_prompts import InvestigationPrompts
from ..tools.registry import get_tool_registry

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
        settings = get_settings()
        self.api_url = settings.LLM_API_URL or "http://localhost:11434/v1"
        self.api_key = settings.LLM_API_KEY or "no-key-required"
        self.model = settings.LLM_MODEL or "llama2"
        self.api_port = settings.WEB_PORT
        # Don't use base_url since we need full URL control
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def investigate_change(self, query: str) -> Dict[str, Any]:
        """Use OpenAI-compatible API for investigation"""
        
        # Get tools from registry
        tool_registry = get_tool_registry()
        tools = tool_registry.get_tool_schemas()
        
        # Get system prompt
        system_prompt = InvestigationPrompts.SYSTEM_PROMPT
        user_prompt = InvestigationPrompts.get_user_prompt(query)
        
        try:
            headers={
                "Content-Type": "application/json"
            }
            if self.api_key != "no-key-required":
                headers["Authorization"] = f"Bearer {self.api_key}"

            # Debug logging
            logger.info(f"Making request to {self.api_url}/chat/completions")
            logger.info(f"Model: {self.model}")
            logger.info(f"Tools count: {len(tools) if tools else 0}")
            
            request_payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "tools": tools,
                "tool_choice": "auto"
            }
            
            # Debug: Check if tools are serializable
            try:
                import json
                json.dumps(request_payload)
                logger.debug("Request payload is JSON serializable")
            except Exception as e:
                logger.error(f"Request payload not JSON serializable: {e}")
                logger.error(f"Problematic tools: {tools}")
                # Try without tools
                request_payload.pop("tools", None)
                request_payload.pop("tool_choice", None)

            response = await self.client.post(
                f"{self.api_url}/chat/completions",
                json=request_payload,
                headers=headers
            )
            
            logger.info(f"Response status: {response.status_code}")
            result = response.json()
            
            # Handle tool calls
            if "choices" in result and len(result["choices"]) > 0:
                message = result["choices"][0]["message"]
                
                if "tool_calls" in message:
                    # Execute tool calls and get results
                    tool_results = await self._execute_tool_calls(message["tool_calls"])
                    
                    # Send results back to LLM for synthesis
                    synthesis_response = await self.client.post(
                        f"{self.api_url}/chat/completions",
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
        tool_registry = get_tool_registry()
        
        import json
        for tool_call in tool_calls:
            function_name = tool_call["function"]["name"]
            arguments = tool_call["function"]["arguments"]
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except Exception as e:
                    logger.error(f"Failed to parse tool arguments for {function_name}: {e}")
                    arguments = {}
            
            # Execute tool using registry
            result = await tool_registry.execute_tool(function_name, **arguments)
            results[function_name] = result
        
        return results
    

    
    def _parse_llm_response(self, response: Dict) -> Dict[str, Any]:
        """Parse LLM response into our format"""
        if "choices" not in response or len(response["choices"]) == 0:
            return {"error": "No choices in response", "details": response}
        
        message = response["choices"][0]["message"]
        content = message.get("content", "")
        
        # Check if content contains XML-style tool calls
        if "<tool_call>" in content:
            logger.warning(f"LLM returned XML-style tool call in content, treating as explanation: {content}")
            return {
                "nodes": [],
                "edges": [],
                "knowledge_gaps": [],
                "explanation": {
                    "reasoning_steps": [f"LLM attempted to call tools but used incorrect format: {content}"],
                    "evidence_sources": [],
                    "confidence_score": 0.3
                }
            }
        
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
                response = await client.get(f"{self.api_url}/models", timeout=5.0)
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
        self.mock_service = None
    
    async def _get_service(self):
        if self.mock_service is None:
            # Import here to avoid circular imports
            from .mock_llm import MockLLMService
            self.mock_service = MockLLMService()
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
        settings = get_settings()
        provider_type = settings.LLM_PROVIDER or "mock"
        
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