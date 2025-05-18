import os
from pathlib import Path
from mcp.server.fastmcp import FastMCP, Context
from mcp.types import TextContent

from src.common.logging import logger
from src.common.utils import ensure_directory
from src.mcp.server.lifespan import file_lifespan

# Create file operations server
file_mcp = FastMCP("File-Operations")

# Configure lifespan
file_mcp.configure_lifespan(file_lifespan)

@file_mcp.tool()
async def write_file(path: str, content: str, ctx: Context) -> dict:
    """Write content to a file at the specified path."""
    logger.info(f"File tool: write_file to path: {path}")
    try:
        base_path = ctx.request_context.lifespan_context.base_path
        full_path = Path(base_path) / path
        
        # Ensure directory exists
        ensure_directory(str(full_path.parent))
        
        # Write content to file
        full_path.write_text(content)
        
        return {
            "success": True,
            "path": str(full_path.absolute())
        }
    except Exception as e:
        logger.error(f"Error writing file: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@file_mcp.tool()
async def read_file(path: str, ctx: Context) -> dict:
    """Read content from a file at the specified path."""
    logger.info(f"File tool: read_file from path: {path}")
    try:
        base_path = ctx.request_context.lifespan_context.base_path
        full_path = Path(base_path) / path
        
        if not full_path.exists():
            return {
                "success": False,
                "error": f"File not found: {path}"
            }
        
        content = full_path.read_text()
        return {
            "success": True,
            "content": content
        }
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@file_mcp.tool()
async def list_files(directory: str = "", ctx: Context) -> dict:
    """List files in a directory."""
    logger.info(f"File tool: list_files in directory: {directory}")
    try:
        base_path = ctx.request_context.lifespan_context.base_path
        full_path = Path(base_path) / directory
        
        if not full_path.exists() or not full_path.is_dir():
            return {
                "success": False,
                "error": f"Directory not found: {directory}"
            }
        
        files = [str(f.relative_to(base_path)) for f in full_path.glob("*")]
        return {
            "success": True,
            "files": files
        }
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@file_mcp.resource("file://{path}")
async def get_file_content(path: str, ctx: Context) -> str:
    """Get content from a file at the specified path as a resource."""
    logger.info(f"File resource: get_file_content from path: {path}")
    try:
        base_path = ctx.request_context.lifespan_context.base_path
        full_path = Path(base_path) / path
        
        if not full_path.exists():
            return f"File not found: {path}"
        
        return full_path.read_text()
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        return f"Error reading file: {str(e)}"