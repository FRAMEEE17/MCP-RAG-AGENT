from typing import Dict, List, Any, Optional

from src.common.logging import logger

class ToolRegistry:
    """Registry for MCP tools."""
    
    def __init__(self):
        self.tools = {}
    
    def register_tool(self, tool: Dict[str, Any], client_name: str):
        """Register a tool with its client."""
        tool_name = tool.get("name")
        if not tool_name:
            logger.warning("Attempted to register tool without a name")
            return
        
        self.tools[tool_name] = {
            "tool": tool,
            "client_name": client_name
        }
        
        logger.debug(f"Registered tool '{tool_name}' from client '{client_name}'")
    
    def get_client_for_tool(self, tool_name: str) -> Optional[str]:
        """Get the client name for a tool."""
        if tool_name in self.tools:
            return self.tools[tool_name]["client_name"]
        return None
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools."""
        return [tool_info["tool"] for tool_info in self.tools.values()]