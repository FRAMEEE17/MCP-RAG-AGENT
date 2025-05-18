import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from mcp.client import Client
from mcp.client.streamable_http import streamablehttp_client

from src.common.logging import logger

class MCPHttpClient:
    """HTTP client for connecting to an MCP server."""
    
    def __init__(self, name: str, url: str, version: str = "0.0.1"):
        self.name = name
        self.url = url
        self.version = version
        self.client = Client({"name": name, "version": version})
        self.read_stream = None
        self.write_stream = None
        self.session_id = None
        self.tools = []
    
    async def init(self):
        """Initialize the connection to the MCP server."""
        try:
            # Connect to the MCP server
            self.read_stream, self.write_stream, self.session_id = await streamablehttp_client(self.url)
            await self.client.connect(self.read_stream, self.write_stream)
            
            # Get available tools
            result = await self.client.list_tools()
            self.tools = result.get("tools", [])
            
            logger.info(f"Connected to HTTP MCP server '{self.name}' at {self.url} with {len(self.tools)} tools")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to HTTP MCP server '{self.name}' at {self.url}: {str(e)}")
            return False
    
    async def close(self):
        """Close the connection to the MCP server."""
        if self.client:
            await self.client.close()
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get the list of tools provided by this MCP server."""
        return self.tools
    
    async def call_tool(self, name: str, params: Dict[str, Any]) -> Any:
        """Call a tool with the given parameters."""
        try:
            logger.debug(f"Calling tool '{name}' on HTTP MCP server '{self.name}' with params: {params}")
            result = await self.client.call_tool({
                "name": name,
                "arguments": params
            })
            return result
        except Exception as e:
            logger.error(f"Error calling tool '{name}' on HTTP MCP server '{self.name}': {str(e)}")
            raise