"""
Tool Registry for Scanner Service

This module provides a registry system for managing LLM tools,
including dynamic discovery, validation, and execution.
"""

import logging
from typing import Dict, Any, List, Callable, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class Tool(ABC):
    """Abstract base class for LLM tools"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description"""
        pass
    
    @property
    @abstractmethod
    def schema(self) -> Dict[str, Any]:
        """JSON schema for tool parameters"""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool"""
        pass

class ToolRegistry:
    """Registry for managing LLM tools"""
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
    
    def register(self, tool: Tool) -> None:
        """Register a tool"""
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get tool by name"""
        return self._tools.get(name)
    
    def get_all_tools(self) -> List[Tool]:
        """Get all registered tools"""
        return list(self._tools.values())
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get all tool schemas for LLM"""
        return [tool.schema for tool in self._tools.values()]
    
    async def execute_tool(self, name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool by name"""
        tool = self.get_tool(name)
        if not tool:
            return {"error": f"Tool '{name}' not found"}
        
        try:
            return await tool.execute(**kwargs)
        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            return {"error": str(e)}

# Global tool registry instance
_tool_registry = ToolRegistry()

def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry"""
    return _tool_registry

def register_tool(tool: Tool) -> Tool:
    """Decorator to register a tool"""
    _tool_registry.register(tool)
    return tool