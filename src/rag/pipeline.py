import os
import json
from typing import List, Dict, Any, Optional, Tuple

from src.common.logging import logger
from src.rag.embed.models import get_embedding_model, EmbeddingModel
from src.rag.retriever.vector_db import FAISSVectorStore

class EmbeddingRetriever:
    """Simple RAG retriever using embeddings."""  
    def __init__(
        self,
        model_name: str = "baai/bge-m3",
        vector_store: Optional[FAISSVectorStore] = None,
        dimension: int = 1024
    ):
        """Initialize the retriever.
        
        Args:
            model_name: Name of the embedding model to use
            vector_store: Optional vector store; if None, a new one is created
            dimension: Dimension of the embeddings
        """
        self.embedding_model = get_embedding_model(model_name)
        self.vector_store = vector_store or FAISSVectorStore(dim=dimension)
        
        logger.info(f"Initialized EmbeddingRetriever with model {model_name}")
    
    async def embed_document(
        self,
        document: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[float]:
        """Embed a document and add it to the vector store."""
        logger.debug(f"Embedding document: {document[:50]}...")
        
        # Get embedding
        embedding = await self.embedding_model.embed_text(document)
        
        # Add to vector store
        self.vector_store.add_document(embedding, document, metadata)
        
        return embedding
    
    async def embed_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> List[List[float]]:
        """Embed multiple documents and add them to the vector store."""
        if metadatas is None:
            metadatas = [{} for _ in documents]
        
        logger.info(f"Embedding {len(documents)} documents")
        
        # Get embeddings for all documents
        embeddings = await self.embedding_model.embed_batch(documents)
        
        # Add to vector store
        self.vector_store.add_documents(embeddings, documents, metadatas)
        
        return embeddings
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant documents for a query."""
        logger.debug(f"Retrieving documents for query: {query}")
        
        # Get query embedding
        query_embedding = await self.embedding_model.embed_text(query)
        
        # Search vector store
        results = self.vector_store.search(query_embedding, top_k)
        
        logger.debug(f"Retrieved {len(results)} documents")
        return results
    
    def save(self, path: str):
        """Save the vector store to disk."""
        self.vector_store.save(path)
    
    @classmethod
    async def load(
        cls,
        path: str,
        model_name: str = "baai/bge-m3"
    ) -> 'EmbeddingRetriever':
        """Load a retriever from disk."""
        # Load vector store
        vector_store = FAISSVectorStore.load(path)
        
        # Create instance
        instance = cls(model_name=model_name, vector_store=vector_store)
        
        return instance


class SimpleRAG:
    def __init__(
        self,
        model_name: str = "baai/bge-m3",
        vector_store_path: Optional[str] = None
    ):
        self.retriever = None
        self.model_name = model_name
        self.vector_store_path = vector_store_path
        
        logger.info(f"Initialized SimpleRAG with model {model_name}")
    
    async def init(self):
        """Initialize the retriever."""
        if self.vector_store_path and os.path.exists(f"{self.vector_store_path}.index"):
            # Load existing vector store
            self.retriever = await EmbeddingRetriever.load(
                self.vector_store_path,
                model_name=self.model_name
            )
            logger.info(f"Loaded vector store from {self.vector_store_path}")
        else:
            # Create new retriever
            self.retriever = EmbeddingRetriever(model_name=self.model_name)
            logger.info("Created new retriever")
        
        return self
    
    async def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ):
        """Add texts to the retriever."""
        if not self.retriever:
            raise ValueError("Retriever not initialized. Call init() first.")
        
        await self.retriever.embed_documents(texts, metadatas)
        
        # Save if path is set
        if self.vector_store_path:
            self.retriever.save(self.vector_store_path)
    
    async def query(
        self,
        query: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """Query the RAG pipeline."""
        if not self.retriever:
            raise ValueError("Retriever not initialized. Call init() first.")
        
        return await self.retriever.retrieve(query, top_k)
    
    async def save(self, path: Optional[str] = None):
        """Save the vector store to disk."""
        if not self.retriever:
            raise ValueError("Retriever not initialized. Call init() first.")
        
        path = path or self.vector_store_path
        if not path:
            raise ValueError("No path specified for saving")
        
        self.retriever.save(path)
        self.vector_store_path = path