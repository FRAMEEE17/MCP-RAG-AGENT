import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.mcp.server.rag import rag_mcp
from src.mcp.server.file import file_mcp
from src.mcp.server.brave_search import brave_search_mcp  # Add import
from src.mcp.server.google_maps import google_maps_mcp    # Add import
from src.common.config import config
from src.common.logging import logger

# Initialize FastAPI app
app = FastAPI(
    title="RAG-MCP API",
    description="Retrieval-Augmented Generation with Model Control Protocol, Search, and Maps",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    logger.info("Starting MCP servers")
    # Start MCP servers
    await rag_mcp.session_manager.run().__aenter__()
    await file_mcp.session_manager.run().__aenter__()
    await brave_search_mcp.session_manager.run().__aenter__()  
    await google_maps_mcp.session_manager.run().__aenter__()  
    logger.info("MCP servers started successfully")

@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down MCP servers")
    # Shutdown MCP servers (in reverse order of startup)
    await google_maps_mcp.session_manager.run().__aexit__(None, None, None) 
    await brave_search_mcp.session_manager.run().__aexit__(None, None, None)  
    await file_mcp.session_manager.run().__aexit__(None, None, None)
    await rag_mcp.session_manager.run().__aexit__(None, None, None)
    logger.info("MCP servers shut down successfully")

# Mount MCP servers to different paths
app.mount("/rag", rag_mcp.streamable_http_app())
app.mount("/file", file_mcp.streamable_http_app())
app.mount("/brave-search", brave_search_mcp.streamable_http_app())  
app.mount("/google-maps", google_maps_mcp.streamable_http_app())   

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server on {config.server.host}:{config.server.port}")

    uvicorn.run(
        "src.app:app",  # Change this to point to the current app
        host=config.server.host,
        port=config.server.port,
        reload=config.server.env == "development"
    )