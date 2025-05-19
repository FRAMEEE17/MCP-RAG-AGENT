import os
import json
import httpx
from mcp.server.fastmcp import FastMCP, Context
from mcp.types import TextContent

from src.common.logging import logger
from src.common.config import config

# Access API key globally
GOOGLE_MAPS_KEY = os.getenv("GOOGLE_MAPS_KEY", "")

# Create Google Maps server
google_maps_mcp = FastMCP("Google-Maps")

@google_maps_mcp.tool()
async def search_places(query: str, location: str, ctx: Context, radius: int = 1500) -> dict:
    """
    Search for places using Google Maps Places API.
    
    Args:
        query: Search query (e.g., "coffee shops")
        location: Location coordinates as "latitude,longitude" (e.g., "13.7563,100.5018")
        radius: Search radius in meters (default: 1500)
    
    Returns:
        Dict containing places search results
    """
    logger.info(f"Google Maps tool: search_places with query: {query}, location: {location}")
    
    try:
        global GOOGLE_MAPS_KEY
        api_key = GOOGLE_MAPS_KEY
        
        if not api_key:
            return {
                "success": False,
                "error": "Google Maps API key not provided"
            }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
                params={
                    "keyword": query,
                    "location": location,
                    "radius": radius,
                    "key": api_key
                }
            )
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Google Maps API returned status code {response.status_code}"
                }
            
            places_results = response.json()
            formatted_results = format_places_results(places_results)
            
            return {
                "success": True,
                "results": formatted_results
            }
            
    except Exception as e:
        error_msg = f"Error searching places: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg
        }

@google_maps_mcp.tool()
async def get_directions(origin: str, destination: str, ctx: Context, mode: str = "driving") -> dict:
    """
    Get directions between two points using Google Maps Directions API.
    
    Args:
        origin: Origin location (address or "latitude,longitude")
        destination: Destination location (address or "latitude,longitude")
        mode: Travel mode (driving, walking, bicycling, transit) (default: driving)
    
    Returns:
        Dict containing directions results
    """
    logger.info(f"Google Maps tool: get_directions from {origin} to {destination} via {mode}")
    
    try:
        global GOOGLE_MAPS_KEY
        api_key = GOOGLE_MAPS_KEY
        
        if not api_key:
            return {
                "success": False,
                "error": "Google Maps API key not provided"
            }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://maps.googleapis.com/maps/api/directions/json",
                params={
                    "origin": origin,
                    "destination": destination,
                    "mode": mode,
                    "key": api_key
                }
            )
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Google Maps API returned status code {response.status_code}"
                }
            
            directions_results = response.json()
            formatted_results = format_directions_results(directions_results)
            
            return {
                "success": True,
                "routes": formatted_results
            }
            
    except Exception as e:
        error_msg = f"Error getting directions: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg
        }

def format_places_results(results):
    """Format the places search results in a more readable structure."""
    formatted = []
    
    for place in results.get("results", []):
        formatted.append({
            "name": place.get("name", ""),
            "address": place.get("vicinity", ""),
            "rating": place.get("rating", "Not rated"),
            "location": {
                "lat": place.get("geometry", {}).get("location", {}).get("lat"),
                "lng": place.get("geometry", {}).get("location", {}).get("lng")
            },
            "place_id": place.get("place_id", ""),
            "types": place.get("types", []),
            "is_open_now": place.get("opening_hours", {}).get("open_now", None)
        })
    
    return formatted

def format_directions_results(results):
    """Format the directions results in a more readable structure."""
    formatted = []
    
    for route in results.get("routes", []):
        legs = route.get("legs", [])
        if not legs:
            continue
            
        leg = legs[0]  # We're only handling the first leg for simplicity
        
        route_summary = {
            "summary": route.get("summary", ""),
            "distance": leg.get("distance", {}).get("text", ""),
            "duration": leg.get("duration", {}).get("text", ""),
            "start_address": leg.get("start_address", ""),
            "end_address": leg.get("end_address", ""),
            "steps": []
        }
        
        for step in leg.get("steps", []):
            route_summary["steps"].append({
                "instruction": step.get("html_instructions", ""),
                "distance": step.get("distance", {}).get("text", ""),
                "duration": step.get("duration", {}).get("text", ""),
                "travel_mode": step.get("travel_mode", "")
            })
        
        formatted.append(route_summary)
    
    return formatted