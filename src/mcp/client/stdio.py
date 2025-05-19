import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from contextlib import AsyncExitStack  # Import from contextlib instead of asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from src.common.logging import logger

class MCPStdioClient:
    """StdIO client for connecting to an MCP server."""
    
    def __init__(self, name: str, command: str, args: List[str], version: str = "0.0.1", env: Optional[Dict[str, str]] = None):
        self.name = name
        self.command = command
        
        # If the command is npx, add the --no-cache flag to avoid EROFS errors in WSL
        if command == "npx":
            # Insert --no-cache at the beginning of args if not already there
            if "--no-cache" not in args:
                args = ["--no-cache"] + args
        
        self.args = args
        self.version = version
        self.env = env  # Store the environment variables
        self.session = None
        self.tools = []
    
    async def init(self):
        """Initialize the connection to the MCP server."""
        try:
            # Set up transport parameters
            server_params = StdioServerParameters(
                command=self.command,
                args=self.args,
                env=self.env  # Pass the environment variables
            )
            
            # Use the async context manager pattern correctly
            self.exit_stack = AsyncExitStack()
            transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            
            # Unpack the transport
            self.read_stream, self.write_stream = transport
            
            # Initialize session
            self.session = ClientSession(self.read_stream, self.write_stream)
            await self.session.initialize()
            
            # Get available tools
            response = await self.session.list_tools()
            self.tools = response.tools
            
            logger.info(f"Connected to stdio MCP server '{self.name}' with {len(self.tools)} tools")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to stdio MCP server '{self.name}': {str(e)}")
            return False
    
    async def close(self):
        """Close the connection to the MCP server."""
        if self.session:
            await self.session.close()
            
        # Clean up the exit stack if it exists
        if hasattr(self, 'exit_stack'):
            await self.exit_stack.aclose()
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get the list of tools provided by this MCP server."""
        return self.tools if self.tools else []
    
    async def call_tool(self, name: str, params: Dict[str, Any]) -> Any:
        """Call a tool with the given parameters."""
        try:
            logger.debug(f"Calling tool '{name}' on stdio MCP server '{self.name}' with params: {params}")
            result = await self.session.call_tool(name=name, arguments=params)
            return result
        except Exception as e:
            logger.error(f"Error calling tool '{name}' on stdio MCP server '{self.name}': {str(e)}")
            raise