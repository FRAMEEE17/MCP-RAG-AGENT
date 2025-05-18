import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.mcp.server.rag import rag_mcp
from src.mcp.server.file import file_mcp
from src.common.config import config
from src.common.logging import logger

# Initialize FastAPI app
app = FastAPI(
    title="RAG-MCP API",
    description="Retrieval-Augmented Generation with Model Control Protocol",
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

# Combined lifespan for FastAPI app to manage MCP servers
@app.on_event("startup")
async def startup():
    logger.info("Starting MCP servers")
    # Start MCP servers
    await rag_mcp.session_manager.run().__aenter__()
    await file_mcp.session_manager.run().__aenter__()
    logger.info("MCP servers started successfully")

@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down MCP servers")
    # Shutdown MCP servers
    await file_mcp.session_manager.run().__aexit__(None, None, None)
    await rag_mcp.session_manager.run().__aexit__(None, None, None)
    logger.info("MCP servers shut down successfully")

# Mount MCP servers to different paths
app.mount("/rag", rag_mcp.streamable_http_app())
app.mount("/file", file_mcp.streamable_http_app())

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server on {config.server.host}:{config.server.port}")
    uvicorn.run(
        "app.main:app",
        host=config.server.host,
        port=config.server.port,
        reload=config.server.env == "development"
    )