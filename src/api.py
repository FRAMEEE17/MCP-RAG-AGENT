from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
import asyncio
import json
from typing import Dict, Any, List, Optional, AsyncGenerator

from src.mcp.client.manager import MCPClientManager
from src.llm.interface import LLMInterface
from src.graph.agent_graph import create_agent_graph, AgentState
from src.common.logging import logger
from src.common.config import config

# Initialize the API
api = FastAPI(
    title="MCP Agent API",
    description="API for interacting with MCP-enabled agent",
    version="0.1.0"
)

# Global storage for client managers and agents
client_managers: Dict[str, MCPClientManager] = {}
agent_graphs: Dict[str, Any] = {}

async def initialize_agent(session_id: str) -> bool:
    """Initialize an agent for a specific session."""
    try:
        # Create MCP client manager for this session
        mcp_manager = MCPClientManager()
        client_managers[session_id] = mcp_manager
        
        # Initialize the HTTP clients for our MCP servers
        base_url = f"http://{config.server.host}:{config.server.port}"
        
        # Connect to all MCP servers
        clients = []
        clients.append(await mcp_manager.create_client_http("rag", f"{base_url}/rag"))
        clients.append(await mcp_manager.create_client_http("file", f"{base_url}/file"))
        clients.append(await mcp_manager.create_client_http("brave-search", f"{base_url}/brave-search"))
        clients.append(await mcp_manager.create_client_http("google-maps", f"{base_url}/google-maps"))
        
        if not all(clients):
            logger.error(f"Failed to connect to one or more MCP servers for session {session_id}")
            return False
        
        # System prompt for the agent
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
        agent_graphs[session_id] = agent_graph
        
        return True
    
    except Exception as e:
        logger.error(f"Error initializing agent for session {session_id}: {str(e)}")
        return False

async def cleanup_agent(session_id: str) -> None:
    """Clean up resources for a specific session."""
    try:
        if session_id in client_managers:
            await client_managers[session_id].close_all()
            del client_managers[session_id]
        
        if session_id in agent_graphs:
            del agent_graphs[session_id]
            
        logger.info(f"Cleaned up resources for session {session_id}")
    
    except Exception as e:
        logger.error(f"Error cleaning up agent for session {session_id}: {str(e)}")

async def process_message_stream(session_id: str, message: str) -> AsyncGenerator[str, None]:
    """Process a message and return a streaming response."""
    try:
        if session_id not in agent_graphs:
            success = await initialize_agent(session_id)
            if not success:
                yield json.dumps({
                    "type": "error",
                    "content": "Failed to initialize agent"
                })
                return
        
        agent_graph = agent_graphs[session_id]
        
        # Create a queue for the streaming results
        queue = asyncio.Queue()
        
        # Create a task to run the agent
        async def run_agent():
            try:
                result_gen = agent_graph.run_stream({"input": message})
                
                async for state in result_gen:
                    # Send intermediate results for content updates
                    if "content" in state:
                        await queue.put(json.dumps({
                            "type": "content",
                            "content": state["content"]
                        }))
                    
                    # Send tool call notifications
                    if "tool_calls" in state and state["tool_calls"]:
                        await queue.put(json.dumps({
                            "type": "tool_call",
                            "tool": state["tool_calls"][0].get("function", {}).get("name", "unknown_tool"),
                            "arguments": state["tool_calls"][0].get("function", {}).get("arguments", "{}")
                        }))
                    
                    # Send tool results
                    if "tool_results" in state and state["tool_results"]:
                        await queue.put(json.dumps({
                            "type": "tool_result",
                            "result": json.dumps(state["tool_results"][0].get("result", {}))
                        }))
                    
                    # Send final content
                    if "final_content" in state:
                        await queue.put(json.dumps({
                            "type": "final",
                            "content": state["final_content"]
                        }))
                
                # Signal the end of the stream
                await queue.put(None)
                
            except Exception as e:
                logger.error(f"Error running agent for session {session_id}: {str(e)}")
                await queue.put(json.dumps({
                    "type": "error",
                    "content": f"Error: {str(e)}"
                }))
                await queue.put(None)
        
        # Start the agent task
        asyncio.create_task(run_agent())
        
        # Yield results from the queue
        while True:
            item = await queue.get()
            if item is None:
                break
            yield f"{item}\n"
    
    except Exception as e:
        logger.error(f"Error processing message for session {session_id}: {str(e)}")
        yield json.dumps({
            "type": "error",
            "content": f"Error: {str(e)}"
        })

@api.post("/chat/{session_id}")
async def chat(session_id: str, request: Request, background_tasks: BackgroundTasks):
    """Chat with the agent using MCP tools."""
    try:
        # Parse the request body
        body = await request.json()
        message = body.get("message", "")
        
        if not message:
            return {"error": "Message is required"}
        
        # Return a streaming response
        return StreamingResponse(
            process_message_stream(session_id, message),
            media_type="text/event-stream"
        )
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return {"error": f"An error occurred: {str(e)}"}

@api.delete("/chat/{session_id}")
async def end_session(session_id: str):
    """End a chat session and clean up resources."""
    background_tasks = BackgroundTasks()
    background_tasks.add_task(cleanup_agent, session_id)
    
    return {"status": "success", "message": f"Session {session_id} is being cleaned up"}

# Health check endpoint
@api.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "servers": ["rag", "file", "brave-search", "google-maps"]}