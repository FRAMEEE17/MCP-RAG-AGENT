from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Dict, Any, Optional

from mcp.server.fastmcp import FastMCP

from src.rag.pipeline import EmbeddingRetriever
from src.common.logging import logger

@dataclass
class RAGContext:
    """Context for RAG MCP server."""
    retriever: EmbeddingRetriever

@asynccontextmanager
async def rag_lifespan(server: FastMCP) -> AsyncIterator[RAGContext]:
    """Manage RAG server lifecycle."""
    # Initialize the retriever
    logger.info("Initializing RAG server lifespan")
    retriever = EmbeddingRetriever("text-embedding-3-small")
    
    try:
        yield RAGContext(retriever=retriever)
    finally:
        # Any cleanup needed
        logger.info("Cleaning up RAG server lifespan")

@dataclass
class FileContext:
    """Context for File MCP server."""
    base_path: str

@asynccontextmanager
async def file_lifespan(server: FastMCP) -> AsyncIterator[FileContext]:
    """Manage File server lifecycle."""
    # Base path for file operations
    import os
    from pathlib import Path
    
    logger.info("Initializing File server lifespan")
    base_path = Path(os.environ.get("FILE_BASE_PATH", str(Path.cwd())))
    
    try:
        yield FileContext(base_path=str(base_path))
    finally:
        # Any cleanup needed
        logger.info("Cleaning up File server lifespan")