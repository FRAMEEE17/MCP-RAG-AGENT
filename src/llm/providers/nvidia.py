import json
from typing import List, Dict, Any, Optional
import openai

from src.common.config import config
from src.common.logging import logger

class NVIDIAProvider:
    """Provider for NVIDIA's LLM API."""
    
    def __init__(self, model: str):
        self.model = model
        self.client = openai.OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=config.nvidia.api_key  # You'll need to add this to your config
        )
    
    async def complete(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Complete a chat sequence using NVIDIA's API."""
        tool_params = {}
        if tools and len(tools) > 0:
            tool_params["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("inputSchema", {})
                    }
                }
                for tool in tools
            ]
        
        try:
            logger.debug(f"Sending request to NVIDIA: model={self.model}, messages={len(messages)}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.6,
                top_p=0.95,
                max_tokens=4096,
                **tool_params
            )
            
            choice = response.choices[0]
            message = choice.message
            
            result = {
                "content": message.content or "",
                "tool_calls": [],
                "finish_reason": choice.finish_reason
            }
            
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    result["tool_calls"].append({
                        "id": tool_call.id,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Error completing chat with NVIDIA: {str(e)}")
            raise