from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph

from src.llm.interface import LLMInterface
from src.mcp.client.manager import MCPClientManager
from src.common.logging import logger

class AgentState(Dict[str, Any]):
    """State object for the agent graph."""
    pass

def create_agent_graph(
    llm: LLMInterface,
    mcp_manager: MCPClientManager
) -> StateGraph:
    """Create the main agent workflow graph."""
    
    # Initialize the state graph
    graph = StateGraph(AgentState)
    
    # Define nodes
    
    async def process_input(state: AgentState) -> AgentState:
        """Process the input prompt."""
        prompt = state.get("input", "")
        logger.debug(f"Processing input: {prompt[:50]}...")
        state["processed_input"] = prompt
        return state
    
    async def generate_response(state: AgentState) -> AgentState:
        """Generate a response from the LLM."""
        prompt = state.get("processed_input", "")
        logger.debug("Generating LLM response")
        response = await llm.chat(prompt)
        
        state["content"] = response.get("content", "")
        state["tool_calls"] = response.get("tool_calls", [])
        
        if state["tool_calls"]:
            logger.debug(f"LLM made {len(state['tool_calls'])} tool calls")
        else:
            logger.debug("LLM made no tool calls")
        
        return state
    
    async def execute_tools(state: AgentState) -> AgentState:
        """Execute any tool calls."""
        tool_calls = state.get("tool_calls", [])
        tool_results = []
        
        for tool_call in tool_calls:
            tool_name = tool_call.get("function", {}).get("name", "")
            tool_args = tool_call.get("function", {}).get("arguments", {})
            tool_id = tool_call.get("id", "")
            
            # Parse arguments if they're a JSON string
            if isinstance(tool_args, str):
                import json
                try:
                    tool_args = json.loads(tool_args)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse tool arguments: {tool_args}")
                    tool_args = {}
            
            try:
                logger.info(f"Executing tool: {tool_name}")
                # Call the tool
                result = await mcp_manager.call_tool(tool_name, tool_args)
                
                # Add result to LLM context
                llm.handle_tool_response(tool_id, str(result))
                
                tool_results.append({
                    "tool_id": tool_id,
                    "tool_name": tool_name,
                    "result": result
                })
                logger.debug(f"Tool execution successful: {tool_name}")
            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {str(e)}")
                # Still add the error to the LLM context
                llm.handle_tool_response(tool_id, f"Error: {str(e)}")
                
                tool_results.append({
                    "tool_id": tool_id,
                    "tool_name": tool_name,
                    "error": str(e)
                })
        
        state["tool_results"] = tool_results
        return state
    
    async def finalize_response(state: AgentState) -> AgentState:
        """Finalize the response after tool execution."""
        # If tools were called, get the final response from the LLM
        if state.get("tool_results"):
            logger.debug("Generating final response after tool execution")
            response = await llm.chat()
            state["final_content"] = response.get("content", "")
            state["final_tool_calls"] = response.get("tool_calls", [])
            
            # Check if we have new tool calls
            if response.get("tool_calls"):
                logger.debug(f"LLM made {len(response.get('tool_calls'))} new tool calls in final response")
                state["has_new_tool_calls"] = True
            else:
                state["has_new_tool_calls"] = False
        else:
            # No tools were called, use the original response
            logger.debug("No tools were called, using original response as final")
            state["final_content"] = state.get("content", "")
            state["final_tool_calls"] = []
            state["has_new_tool_calls"] = False
        
        return state
    
    # Add nodes to the graph
    graph.add_node("process_input", process_input)
    graph.add_node("generate_response", generate_response)
    graph.add_node("execute_tools", execute_tools)
    graph.add_node("finalize_response", finalize_response)
    
    # Define edges
    graph.add_edge("process_input", "generate_response")
    
    # Conditional edge: if there are tool calls, execute them
    def should_execute_tools(state: AgentState) -> str:
        return "execute_tools" if state.get("tool_calls") else "finalize_response"
    
    graph.add_conditional_edges(
        "generate_response",
        should_execute_tools
    )
    
    graph.add_edge("execute_tools", "finalize_response")
    
    # Conditional edge: if there are new tool calls in the final response, go back to execute tools
    def should_loop_execution(state: AgentState) -> str:
        if state.get("has_new_tool_calls"):
            # We need to update the state for the next iteration
            state["tool_calls"] = state.get("final_tool_calls", [])
            return "execute_tools"
        else:
            return "end"
    
    graph.add_conditional_edges(
        "finalize_response",
        should_loop_execution
    )
    
    # Set the entry point
    graph.set_entry_point("process_input")
    
    return graph