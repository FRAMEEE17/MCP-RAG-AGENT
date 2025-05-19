# demo.py
import asyncio
import os
import json
from src.mcp.client.manager import MCPClientManager
from src.llm.interface import LLMInterface
from src.graph.agent_graph import create_agent_graph
from src.common.logging import logger
from src.common.config import config

async def run_demo():
    """Run a demo that showcases MCP capabilities with Brave Search and Google Maps."""
    try:
        # Create MCP client manager
        mcp_manager = MCPClientManager()
        
        # Initialize the HTTP clients for our MCP servers
        base_url = f"http://{config.server.host}:{config.server.port}"
        
        # Connect to RAG MCP
        rag_client = await mcp_manager.create_client_http(
            name="rag",
            url=f"{base_url}/rag"
        )
        
        # Connect to File MCP
        file_client = await mcp_manager.create_client_http(
            name="file",
            url=f"{base_url}/file"
        )
        
        # Connect to Brave Search MCP
        brave_search_client = await mcp_manager.create_client_http(
            name="brave-search",
            url=f"{base_url}/brave-search"
        )
        
        # Connect to Google Maps MCP
        google_maps_client = await mcp_manager.create_client_http(
            name="google-maps",
            url=f"{base_url}/google-maps"
        )
        
        if not all([rag_client, file_client, brave_search_client, google_maps_client]):
            logger.error("Failed to connect to one or more MCP servers")
            return
        
        # System prompt that instructs the model how to use the tools
        system_prompt = """
        You are an intelligent assistant with access to various tools:
        - Brave Search: For finding information from the web
        - Google Maps: For location-based searches and directions
        - File Operations: For reading and writing files
        - RAG: For retrieving relevant knowledge

        Use these tools to help the user with their requests. Think carefully about which tool to use based on the user's query.
        For search-related queries, use the Brave Search tool.
        For location, navigation, or place-related queries, use the Google Maps tools.
        For document-related tasks, use the File tools.
        For questions that might be answered by existing knowledge, use the RAG tools.
        """
        
        # Initialize LLM with all available tools
        llm = LLMInterface(
            provider="openai",
            model="gpt-4o-mini",
            system_prompt=system_prompt,
            tools=mcp_manager.get_all_tools()
        )
        
        # Create the agent graph
        agent_graph = create_agent_graph(llm, mcp_manager)
        
        # Define demo prompts
        demo_prompts = [
            "What are the latest news about artificial intelligence?",
            "Find coffee shops near CentralWorld in Bangkok and give me directions to the best-rated one.",
            "Search for information about Model Control Protocol and save a summary to a file called mcp_summary.md."
        ]
        
        # Run the agent with each prompt
        for i, prompt in enumerate(demo_prompts):
            print(f"\n{'='*80}\nDemo {i+1}: {prompt}\n{'='*80}\n")
            # Process the prompt through the agent graph
            result = await agent_graph.run({"input": prompt})
            print(f"\nFinal Response: {result.get('final_content', '')}")
        
        # Clean up resources
        await mcp_manager.close_all()
        
    except Exception as e:
        logger.error(f"Error running demo: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(run_demo())