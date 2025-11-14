"""Tool registry for managing available tools."""

from typing import Dict, List, Optional, Type
from .base import BaseTool, ToolResult
from agent.core.exceptions import ToolNotFoundError
import logging

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for managing and accessing agent tools."""

    def __init__(self):
        """Initialize tool registry."""
        self._tools: Dict[str, BaseTool] = {}
        self._categories: Dict[str, List[str]] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a new tool.

        Args:
            tool: Tool instance to register

        Raises:
            ValueError: If tool with same name already exists
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")

        self._tools[tool.name] = tool

        # Add to category
        category = tool.category
        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(tool.name)

        logger.info(f"Registered tool: {tool.name} (category: {category})")

    def unregister(self, tool_name: str) -> None:
        """Unregister a tool.

        Args:
            tool_name: Name of tool to unregister

        Raises:
            ToolNotFoundError: If tool not found
        """
        if tool_name not in self._tools:
            raise ToolNotFoundError(f"Tool '{tool_name}' not found")

        tool = self._tools[tool_name]
        category = tool.category

        # Remove from tools
        del self._tools[tool_name]

        # Remove from category
        if category in self._categories:
            self._categories[category].remove(tool_name)
            if not self._categories[category]:
                del self._categories[category]

        logger.info(f"Unregistered tool: {tool_name}")

    def get(self, tool_name: str) -> BaseTool:
        """Get tool by name.

        Args:
            tool_name: Name of tool to retrieve

        Returns:
            Tool instance

        Raises:
            ToolNotFoundError: If tool not found
        """
        if tool_name not in self._tools:
            raise ToolNotFoundError(f"Tool '{tool_name}' not found")
        return self._tools[tool_name]

    def has(self, tool_name: str) -> bool:
        """Check if tool exists in registry.

        Args:
            tool_name: Name of tool to check

        Returns:
            True if tool exists
        """
        return tool_name in self._tools

    def list_tools(self, category: Optional[str] = None) -> List[BaseTool]:
        """List all registered tools, optionally filtered by category.

        Args:
            category: Optional category to filter by

        Returns:
            List of tool instances
        """
        if category:
            if category not in self._categories:
                return []
            tool_names = self._categories[category]
            return [self._tools[name] for name in tool_names]

        return list(self._tools.values())

    def list_tool_names(self, category: Optional[str] = None) -> List[str]:
        """List names of registered tools.

        Args:
            category: Optional category to filter by

        Returns:
            List of tool names
        """
        tools = self.list_tools(category)
        return [tool.name for tool in tools]

    def list_categories(self) -> List[str]:
        """List all tool categories.

        Returns:
            List of category names
        """
        return list(self._categories.keys())

    def execute(self, tool_name: str, **kwargs) -> ToolResult:
        """Execute a tool by name.

        Args:
            tool_name: Name of tool to execute
            **kwargs: Parameters for tool execution

        Returns:
            ToolResult

        Raises:
            ToolNotFoundError: If tool not found
        """
        tool = self.get(tool_name)
        logger.info(f"Executing tool: {tool_name}")
        return tool.run(**kwargs)

    def get_tool_info(self, tool_name: str) -> Dict:
        """Get information about a tool.

        Args:
            tool_name: Name of tool

        Returns:
            Dict with tool information

        Raises:
            ToolNotFoundError: If tool not found
        """
        tool = self.get(tool_name)
        return tool.to_dict()

    def get_all_tools_info(self) -> List[Dict]:
        """Get information about all registered tools.

        Returns:
            List of dicts with tool information
        """
        return [tool.to_dict() for tool in self._tools.values()]

    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
        self._categories.clear()
        logger.info("Cleared all tools from registry")

    def get_stats(self) -> Dict:
        """Get statistics for all tools.

        Returns:
            Dict with tool statistics
        """
        return {
            tool_name: tool.get_stats()
            for tool_name, tool in self._tools.items()
        }

    def __len__(self) -> int:
        """Number of registered tools."""
        return len(self._tools)

    def __contains__(self, tool_name: str) -> bool:
        """Check if tool exists (supports 'in' operator)."""
        return tool_name in self._tools

    def __str__(self) -> str:
        """String representation."""
        return f"ToolRegistry({len(self._tools)} tools, {len(self._categories)} categories)"

    def __repr__(self) -> str:
        """Detailed string representation."""
        tools_by_category = {
            cat: len(tools) for cat, tools in self._categories.items()
        }
        return f"<ToolRegistry(tools={len(self._tools)}, categories={tools_by_category})>"


# Singleton instance
_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """Get or create singleton tool registry.

    Returns:
        ToolRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


def register_tool(tool: BaseTool) -> None:
    """Register a tool to the global registry.

    Args:
        tool: Tool instance to register
    """
    registry = get_registry()
    registry.register(tool)


def get_tool(tool_name: str) -> BaseTool:
    """Get tool from global registry.

    Args:
        tool_name: Name of tool

    Returns:
        Tool instance
    """
    registry = get_registry()
    return registry.get(tool_name)


def execute_tool(tool_name: str, **kwargs) -> ToolResult:
    """Execute tool from global registry.

    Args:
        tool_name: Name of tool
        **kwargs: Tool parameters

    Returns:
        ToolResult
    """
    registry = get_registry()
    return registry.execute(tool_name, **kwargs)
