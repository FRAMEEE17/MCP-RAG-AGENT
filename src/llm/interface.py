from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from src.common.logging import logger

class ToolCall(BaseModel):
    """Represents a tool call from an LLM."""
    id: str
    function: Dict[str, Any]

class LLMInterface:
    """Unified interface for LLM providers."""
    def __init__(
        self,
        provider: str,
        model: str,
        system_prompt: str = "",
        tools: List[Dict] = None,
        context: str = "",
    ):
        self.provider = provider
        self.model = model
        self.messages = []
        self.tools = tools or []
        
        # Add system prompt and context
        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})
        if context:
            self.messages.append({"role": "user", "content": context})
            
        # Initialize the appropriate provider
        if provider == "openai":
            from .providers.openai import OpenAIProvider
            self.provider_instance = OpenAIProvider(model)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
        logger.info(f"Initialized LLMInterface with provider: {provider}, model: {model}")
    
    async def chat(self, prompt: Optional[str] = None) -> Dict[str, Any]:
        """Send a message to the LLM and get a response with potential tool calls."""
        if prompt:
            logger.debug(f"Adding user prompt: {prompt[:50]}...")
            self.messages.append({"role": "user", "content": prompt})
            
        response = await self.provider_instance.complete(
            messages=self.messages,
            tools=self.tools
        )
        
        # Add assistant's response to message history
        self.messages.append({
            "role": "assistant",
            "content": response.get("content", ""),
            "tool_calls": response.get("tool_calls", [])
        })
        
        return response
    
    def handle_tool_response(self, tool_call_id: str, tool_output: str):
        """Handle a tool's response and add it to the message history."""
        logger.debug(f"Handling tool response for tool call ID: {tool_call_id}")
        self.messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": tool_output
        })