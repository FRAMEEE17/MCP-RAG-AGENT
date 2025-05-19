import asyncio
from typing import Dict, List, Any, Optional

from src.common.logging import logger
from src.mcp.registry import ToolRegistry
from src.mcp.client.http import MCPHttpClient
from src.mcp.client.stdio import MCPStdioClient

class MCPClientManager:
    """Manages multiple MCP client connections."""
    
    def __init__(self):
        self.clients = {}
        self.registry = ToolRegistry()
    
    async def create_client_stdio(
        self, 
        name: str, 
        command: str, 
        args: List[str], 
        version: str = "0.0.1",
        env: Optional[Dict[str, str]] = None
    ) -> Any:
        """Create and initialize a new stdio MCP client."""
        client = MCPStdioClient(name, command, args, version, env)
        success = await client.init()
        
        if not success:
            logger.warning(f"Failed to initialize stdio MCP client '{name}'")
            return None
            
        self.clients[name] = client
        
        # Register all tools from this client
        for tool in client.get_tools():
            self.registry.register_tool(tool, name)
            
        logger.info(f"Initialized stdio MCP client '{name}' with {len(client.get_tools())} tools")
        return client
    
    async def create_client_http(
        self, 
        name: str, 
        url: str, 
        version: str = "0.0.1"
    ) -> Any:
        """Create and initialize a new HTTP MCP client."""
        client = MCPHttpClient(name, url, version)
        success = await client.init()
        
        if not success:
            logger.warning(f"Failed to initialize HTTP MCP client '{name}'")
            return None
        
        self.clients[name] = client
        
        # Register all tools from this client
        for tool in client.get_tools():
            self.registry.register_tool(tool, name)
            
        logger.info(f"Initialized HTTP MCP client '{name}' with {len(client.get_tools())} tools")
        return client
    
    def get_client(self, name: str) -> Optional[Any]:
        """Get an existing client by name."""
        return self.clients.get(name)
    
    def get_client_for_tool(self, tool_name: str) -> Optional[Any]:
        """Find the client that provides a specific tool."""
        client_name = self.registry.get_client_for_tool(tool_name)
        if client_name:
            return self.clients.get(client_name)
        return None
    
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Call a tool by name with the given parameters."""
        client = self.get_client_for_tool(tool_name)
        if not client:
            logger.error(f"No client found for tool: {tool_name}")
            raise ValueError(f"No client found for tool: {tool_name}")
        
        logger.debug(f"Calling tool '{tool_name}' with parameters: {params}")
        return await client.call_tool(tool_name, params)
    
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """Get all available tools from all clients."""
        return self.registry.list_tools()
    
    async def close_all(self):
        """Close all client connections."""
        for name, client in self.clients.items():
            logger.debug(f"Closing MCP client: {name}")
            await client.close()
        logger.info("Closed all MCP clients")