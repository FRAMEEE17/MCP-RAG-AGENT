import os
import json
import asyncio
import subprocess
from typing import List, Dict, Any, Optional
from mcp.client import Client
from mcp.client.stdio import StdioClientTransport, stdio_client

from src.common.logging import logger

class MCPStdioClient:
    """StdIO client for connecting to an MCP server."""
    
    def __init__(self, name: str, command: str, args: List[str], version: str = "0.0.1"):
        self.name = name
        self.command = command
        self.args = args
        self.version = version
        self.client = Client({"name": name, "version": version})
        self.transport = None
        self.read_stream = None
        self.write_stream = None
        self.tools = []
    
    async def init(self):
        """Initialize the connection to the MCP server."""
        try:
            # Set up transport
            self.transport = StdioClientTransport({
                "command": self.command,
                "args": self.args
            })
            
            # Connect to the MCP server
            self.read_stream, self.write_stream = await stdio_client(
                {
                    "command": self.command,
                    "args": self.args
                }
            )
            
            await self.client.connect(self.read_stream, self.write_stream)
            
            # Get available tools
            result = await self.client.list_tools()
            self.tools = result.get("tools", [])
            
            logger.info(f"Connected to stdio MCP server '{self.name}' with {len(self.tools)} tools")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to stdio MCP server '{self.name}': {str(e)}")
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
            logger.debug(f"Calling tool '{name}' on stdio MCP server '{self.name}' with params: {params}")
            result = await self.client.call_tool({
                "name": name,
                "arguments": params
            })
            return result
        except Exception as e:
            logger.error(f"Error calling tool '{name}' on stdio MCP server '{self.name}': {str(e)}")
            raise