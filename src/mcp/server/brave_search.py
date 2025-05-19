import os
import json
import httpx
from mcp.server.fastmcp import FastMCP, Context
from mcp.types import TextContent

from src.common.logging import logger
from src.common.config import config

# Access API key globally
BRAVE_SEARCH_KEY = os.getenv("BRAVE_SEARCH_KEY", "")

# Create Brave Search server
brave_search_mcp = FastMCP("Brave-Search")

@brave_search_mcp.tool()
async def search_web(query: str, ctx: Context, count: int = 5) -> dict:
    """
    Search the web using Brave Search API.
    
    Args:
        query: The search query
        count: Number of results to return (default: 5)
    
    Returns:
        Dict containing search results
    """
    logger.info(f"Brave Search tool: search_web with query: {query}, count: {count}")
    
    try:
        global BRAVE_SEARCH_KEY
        api_key = BRAVE_SEARCH_KEY
        
        if not api_key:
            return {
                "success": False,
                "error": "Brave Search API key not provided"
            }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers={"Accept": "application/json", "X-Subscription-Token": api_key},
                params={"q": query, "count": count}
            )
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Brave Search API returned status code {response.status_code}"
                }
            
            search_results = response.json()
            formatted_results = format_search_results(search_results)
            
            return {
                "success": True,
                "results": formatted_results
            }
            
    except Exception as e:
        error_msg = f"Error during Brave search: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg
        }

def format_search_results(results):
    """Format the search results in a more readable structure."""
    formatted = []
    
    if not results.get("web", {}).get("results"):
        return formatted
    
    for web_result in results.get("web", {}).get("results", []):
        formatted.append({
            "title": web_result.get("title", ""),
            "description": web_result.get("description", ""),
            "url": web_result.get("url", ""),
            "is_family_friendly": web_result.get("is_family_friendly", True),
            "published_date": web_result.get("published_date", "")
        })
    
    return formatted