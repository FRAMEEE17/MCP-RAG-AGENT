import os
import json
import asyncio
from typing import List, Dict, Any, Optional
import httpx

from src.common.logging import logger

class MCPHttpClient:
    """HTTP client for connecting to an MCP server."""
    
    def __init__(self, name: str, url: str, version: str = "0.0.1"):
        self.name = name
        self.url = url
        self.version = version
        self.client = httpx.AsyncClient()
        self.session_id = None
        self.tools = []
    
    async def init(self):
        """Initialize the connection to the MCP server."""
        try:
            # Connect to the MCP server
            response = await self.client.post(
                f"{self.url}/initialize",
                json={
                    "client": {
                        "name": self.name,
                        "version": self.version
                    }
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to initialize connection to HTTP MCP server '{self.name}': {response.text}")
                return False
            
            init_data = response.json()
            self.session_id = init_data.get("session_id")
            
            # Get available tools
            tools_response = await self.client.post(
                f"{self.url}/list_tools",
                json={}
            )
            
            if tools_response.status_code != 200:
                logger.error(f"Failed to get tools from HTTP MCP server '{self.name}': {tools_response.text}")
                return False
            
            tools_data = tools_response.json()
            self.tools = tools_data.get("tools", [])
            
            logger.info(f"Connected to HTTP MCP server '{self.name}' at {self.url} with {len(self.tools)} tools")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to HTTP MCP server '{self.name}' at {self.url}: {str(e)}")
            return False
    
    async def close(self):
        """Close the connection to the MCP server."""
        await self.client.aclose()
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get the list of tools provided by this MCP server."""
        return self.tools
    
    async def call_tool(self, name: str, params: Dict[str, Any]) -> Any:
        """Call a tool with the given parameters."""
        try:
            logger.debug(f"Calling tool '{name}' on HTTP MCP server '{self.name}' with params: {params}")
            
            response = await self.client.post(
                f"{self.url}/call_tool",
                json={
                    "name": name,
                    "arguments": params
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to call tool: {response.text}")
            
            result = response.json()
            return result
        except Exception as e:
            logger.error(f"Error calling tool '{name}' on HTTP MCP server '{self.name}': {str(e)}")
            raise