# from typing import Dict, Any, List, Optional
# import asyncio

# from src.llm.interface import LLMInterface
# from src.mcp.client.manager import MCPClientManager
# from src.graph.agent_graph import create_agent_graph
# from src.common.logging import logger

# class Agent:
#     """Agent that combines LLMs with MCP tools and RAG capabilities."""
    
#     def __init__(
#         self, 
#         model: str, 
#         mcp_manager: MCPClientManager,
#         system_prompt: str = "",
#         context: str = ""
#     ):
#         self.model = model
#         self.mcp_manager = mcp_manager
#         self.system_prompt = system_prompt
#         self.context = context
#         self.llm = None
#         self.graph = None
#         logger.info(f"Initialized Agent with model: {model}")
    
#     async def init(self):
#         """Initialize the agent and its components."""
#         # Get all available tools from the MCP manager
#         tools = self.mcp_manager.get_all_tools()
#         logger.info(f"Agent loaded {len(tools)} tools from MCP manager")
        
#         # Determine provider based on model name
#         provider = "openai"
#         if self.model.startswith("claude"):
#             provider = "anthropic"
#         elif self.model.startswith("nvidia/"):  
#             provider = "nvidia"
        
#         # Initialize the LLM with tools
#         self.llm = LLMInterface(
#             provider=provider,
#             model=self.model,
#             system_prompt=self.system_prompt,
#             tools=tools,
#             context=self.context
#         )
        
#         # Create the agent workflow graph
#         self.graph = create_agent_graph(self.llm, self.mcp_manager)
#         logger.info("Agent initialization complete")
        
#         return self
    
#     async def process(self, prompt: str) -> str:
#         """Process a user prompt through the agent's graph."""
#         if not self.graph:
#             logger.error("Agent not initialized. Call init() first.")
#             raise ValueError("Agent not initialized. Call init() first.")
        
#         logger.info(f"Processing prompt: {prompt[:50]}...")
        
#         # Run the agent graph with the input prompt
#         result = await self.graph.run({"input": prompt})
        
#         # Return the final content from the graph
#         return result.get("final_content", "")
    
#     async def close(self):
#         """Clean up resources."""
#         logger.info("Closing agent resources")
#         await self.mcp_manager.close_all()