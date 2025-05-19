from mcp.server.fastmcp import FastMCP, Context
from mcp.types import TextContent

from src.common.logging import logger
from src.rag.pipeline import EmbeddingRetriever

# Create a global retriever instance with BGE-M3
_retriever = EmbeddingRetriever("baai/bge-m3")

# Create RAG-specific server
rag_mcp = FastMCP("RAG-Services")

@rag_mcp.tool()
async def retrieve_documents(query: str, ctx: Context, top_k: int = 3) -> list:
    """Retrieve relevant documents based on the query."""
    logger.info(f"RAG tool: retrieve_documents with query: {query}, top_k: {top_k}")
    global _retriever
    docs = await _retriever.retrieve(query, top_k)
    return docs

@rag_mcp.tool()
async def embed_document(document: str, ctx: Context, metadata: dict = None) -> dict:
    """Embed a document and store it in the vector store."""
    logger.info(f"RAG tool: embed_document with document length: {len(document)}")
    global _retriever
    embedding = await _retriever.embed_document(document, metadata)
    return {"success": True, "message": "Document embedded successfully"}

# Proper implementation for the resource definition
@rag_mcp.resource("knowledge://{query}")
async def get_knowledge(query: str) -> str:
    """Get knowledge about a specific query."""
    logger.info(f"RAG resource: get_knowledge with query: {query}")
    global _retriever
    docs = await _retriever.retrieve(query, top_k=1)
    if docs:
        return docs[0]
    return "No relevant information found."