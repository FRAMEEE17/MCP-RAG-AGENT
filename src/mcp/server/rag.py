from mcp.server.fastmcp import FastMCP, Context
from mcp.types import TextContent

from src.common.logging import logger
from src.mcp.server.lifespan import rag_lifespan

# Create RAG-specific server
rag_mcp = FastMCP("RAG-Services")

# Configure lifespan
rag_mcp.configure_lifespan(rag_lifespan)

@rag_mcp.tool()
async def retrieve_documents(query: str, top_k: int = 3, ctx: Context) -> list:
    """Retrieve relevant documents based on the query."""
    logger.info(f"RAG tool: retrieve_documents with query: {query}, top_k: {top_k}")
    retriever = ctx.request_context.lifespan_context.retriever
    docs = await retriever.retrieve(query, top_k)
    return docs

@rag_mcp.tool()
async def embed_document(document: str, metadata: dict = None, ctx: Context) -> dict:
    """Embed a document and store it in the vector store."""
    logger.info(f"RAG tool: embed_document with document length: {len(document)}")
    retriever = ctx.request_context.lifespan_context.retriever
    embedding = await retriever.embed_document(document, metadata)
    return {"success": True, "message": "Document embedded successfully"}

@rag_mcp.resource("knowledge://{query}")
async def get_knowledge(query: str, ctx: Context) -> str:
    """Get knowledge about a specific query."""
    logger.info(f"RAG resource: get_knowledge with query: {query}")
    retriever = ctx.request_context.lifespan_context.retriever
    docs = await retriever.retrieve(query, top_k=1)
    if docs:
        return docs[0]
    return "No relevant information found."