import os
import json
import httpx
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

from src.common.config import config
from src.common.logging import logger

class EmbeddingModel(ABC):
    """Base class for embedding models."""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
    
    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Embed a single text into a vector representation."""
        pass
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts into vector representations."""
        # Default implementation: process one by one
        embeddings = []
        for text in texts:
            embedding = await self.embed_text(text)
            embeddings.append(embedding)
        return embeddings

class OpenAIEmbeddingModel(EmbeddingModel):
    """Embedding model using OpenAI's API."""
    def __init__(self, model_name: str = "text-embedding-3-small"):
        super().__init__(model_name)
        self.api_key = config.openai.api_key
        self.base_url = config.openai.base_url
        
        if not self.api_key:
            raise ValueError("OpenAI API key is not set")
    
    async def embed_text(self, text: str) -> List[float]:
        """Embed a single text using the OpenAI API."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model_name,
                    "input": text
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                logger.error(f"OpenAI API error: {response.status_code}: {response.text}")
                raise ValueError(f"API error: {response.status_code}: {response.text}")
            
            data = response.json()
            return data["data"][0]["embedding"]
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts in a single API call."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model_name,
                    "input": texts
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                logger.error(f"OpenAI API error: {response.status_code}: {response.text}")
                raise ValueError(f"API error: {response.status_code}: {response.text}")
            
            data = response.json()
            embeddings = sorted(data["data"], key=lambda x: x["index"])
            return [item["embedding"] for item in embeddings]

class NVIDIAEmbeddingModel(EmbeddingModel):
    """Embedding model using NVIDIA's API."""
    def __init__(self, model_name: str = "baai/bge-m3"):
        super().__init__(model_name)
        self.api_key = config.nvidia.api_key
        self.base_url = "https://integrate.api.nvidia.com/v1"
        
        if not self.api_key:
            raise ValueError("NVIDIA API key is not set")
    
    async def embed_text(self, text: str) -> List[float]:
        """Embed a single text using the NVIDIA API."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model_name,
                    "input": text
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                logger.error(f"NVIDIA API error: {response.status_code}: {response.text}")
                raise ValueError(f"API error: {response.status_code}: {response.text}")
            
            data = response.json()
            return data["data"][0]["embedding"]
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts in a single API call."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model_name,
                    "input": texts
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                logger.error(f"NVIDIA API error: {response.status_code}: {response.text}")
                raise ValueError(f"API error: {response.status_code}: {response.text}")
            
            data = response.json()
            embeddings = sorted(data["data"], key=lambda x: x["index"])
            return [item["embedding"] for item in embeddings]

def get_embedding_model(model_name: str) -> EmbeddingModel:
    """Factory function to get an embedding model."""
    if model_name.startswith("text-embedding"):
        return OpenAIEmbeddingModel(model_name)
    elif model_name.startswith("nvidia/"):
        return NVIDIAEmbeddingModel(model_name)
    else:
        # Check if NVIDIA API key is available
        if config.nvidia.api_key:
            return NVIDIAEmbeddingModel("baai/bge-m3")
        # Check if OpenAI API key is available
        elif config.openai.api_key:
            return OpenAIEmbeddingModel("text-embedding-3-small")
        else:
            raise ValueError("No API keys available for embedding models")