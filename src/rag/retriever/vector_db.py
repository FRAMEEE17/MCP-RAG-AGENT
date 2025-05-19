import os
import json
import faiss
import numpy as np
from typing import List, Dict, Any, Optional, Tuple

from src.common.logging import logger

class FAISSVectorStore:
    def __init__(self, dim: int = 1024):
        """
        Args:
            dim: Dimension of the embeddings
        """
        self.dim = dim
        self.index = faiss.IndexFlatL2(dim)  # Simple L2 distance index
        self.documents = []  # Store documents with their metadata
        
        logger.info(f"Initialized FAISS vector store with dimension {dim}")
    
    def add_document(
        self, 
        embedding: List[float], 
        text: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Add a document to the vector store."""
        if len(embedding) != self.dim:
            raise ValueError(f"Embedding dimension mismatch: got {len(embedding)}, expected {self.dim}")
        
        # Convert to numpy array
        embedding_np = np.array([embedding], dtype=np.float32)
        
        # Add to index
        doc_id = len(self.documents)
        self.index.add(embedding_np)
        
        # Store document text and metadata
        self.documents.append({
            "id": doc_id,
            "text": text,
            "metadata": metadata or {}
        })
        
        logger.debug(f"Added document {doc_id} to vector store")
        return doc_id
    
    def add_documents(
        self, 
        embeddings: List[List[float]], 
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> List[int]:
        """Add multiple documents to the vector store."""
        if metadatas is None:
            metadatas = [{} for _ in texts]
        
        if not (len(embeddings) == len(texts) == len(metadatas)):
            raise ValueError("Number of embeddings, texts, and metadatas must match")
        
        doc_ids = []
        for i, (embedding, text, metadata) in enumerate(zip(embeddings, texts, metadatas)):
            doc_id = self.add_document(embedding, text, metadata)
            doc_ids.append(doc_id)
        
        return doc_ids
    
    def search(
        self, 
        query_embedding: List[float], 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        if len(query_embedding) != self.dim:
            raise ValueError(f"Query embedding dimension mismatch: got {len(query_embedding)}, expected {self.dim}")
        
        if not self.documents:
            logger.warning("Vector store is empty, no documents to search")
            return []
        
        # Convert to numpy array
        query_embedding_np = np.array([query_embedding], dtype=np.float32)
        
        # Adjust top_k if we have fewer documents
        top_k = min(top_k, len(self.documents))
        
        # Search
        distances, indices = self.index.search(query_embedding_np, top_k)
        
        # Get documents
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < 0 or idx >= len(self.documents):
                continue  # Skip invalid indices
                
            doc = self.documents[idx]
            results.append({
                "id": doc["id"],
                "text": doc["text"],
                "metadata": doc["metadata"],
                "score": float(1.0 / (1.0 + distance))  # Convert distance to similarity score
            })
        
        return results
    
    def save(self, path: str):
        """Save the vector store to disk."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Save index
        index_path = f"{path}.index"
        faiss.write_index(self.index, index_path)
        
        # Save documents
        docs_path = f"{path}.json"
        with open(docs_path, "w") as f:
            json.dump(self.documents, f)
        
        logger.info(f"Saved vector store to {path}")
    
    @classmethod
    def load(cls, path: str) -> 'FAISSVectorStore':
        """Load a vector store from disk."""
        # Load index
        index_path = f"{path}.index"
        index = faiss.read_index(index_path)
        
        # Load documents
        docs_path = f"{path}.json"
        with open(docs_path, "r") as f:
            documents = json.load(f)
        
        # Create instance
        instance = cls(dim=index.d)
        instance.index = index
        instance.documents = documents
        
        logger.info(f"Loaded vector store from {path} with {len(documents)} documents")
        return instance