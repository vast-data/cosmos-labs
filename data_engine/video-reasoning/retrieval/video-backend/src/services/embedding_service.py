"""
Embedding service for generating text embeddings using NVIDIA NIM
"""
import logging
import requests
import time
from typing import List
from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmbeddingService:
    """Service for generating embeddings using NVIDIA NIM"""
    
    def __init__(self):
        self.settings = settings
        
        # Use NVIDIA Cloud if default is enabled
        if self.settings.embedding_default:
            self.base_url = "https://integrate.api.nvidia.com/v1"
            logger.info("Using NVIDIA Cloud API for embeddings")
        else:
            self.base_url = f"{self.settings.embedding_http_scheme}://{self.settings.embedding_host}:{self.settings.embedding_port}/v1"
            logger.info(f"Using custom NVIDIA NIM endpoint: {self.base_url}")
        
        self.embedding_url = f"{self.base_url}/embeddings"
        self.model = self.settings.embedding_model
        self.dimensions = self.settings.embedding_dimensions
    
    def generate_embedding(self, text: str, input_type: str = "query") -> tuple[List[float], float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
            input_type: "query" for search queries, "passage" for documents
            
        Returns:
            Tuple of (embedding vector, generation time in ms)
            
        Raises:
            Exception if embedding generation fails
        """
        return self.generate_embeddings([text], input_type=input_type)[0]
    
    def generate_embeddings(self, texts: List[str], input_type: str = "query") -> List[tuple[List[float], float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            input_type: "query" for search queries, "passage" for documents
            
        Returns:
            List of tuples (embedding vector, generation time in ms)
            
        Raises:
            Exception if embedding generation fails
        """
        start_time = time.time()
        
        try:
            headers = {
                "Content-Type": "application/json"
            }
            
            # Add API key if using NVIDIA Cloud
            if self.settings.embedding_default and self.settings.nvidia_api_key:
                headers["Authorization"] = f"Bearer {self.settings.nvidia_api_key}"
            
            payload = {
                "input": texts,
                "model": self.model,
                "encoding_format": "float",
                "input_type": input_type  # Required for asymmetric models
            }
            
            logger.debug(f"Requesting embeddings for {len(texts)} texts")
            logger.debug(f"URL: {self.embedding_url}")
            logger.debug(f"Model: {self.model}")
            
            response = requests.post(
                self.embedding_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"Embedding API error: {response.status_code} - {response.text}")
                raise Exception(f"Embedding API returned {response.status_code}: {response.text}")
            
            result = response.json()
            embeddings_data = result.get("data", [])
            
            if not embeddings_data:
                raise Exception("No embeddings returned from API")
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            # Extract embeddings and create result tuples
            results = []
            for item in embeddings_data:
                embedding = item.get("embedding", [])
                if len(embedding) != self.dimensions:
                    logger.warning(f"Unexpected embedding dimension: {len(embedding)} (expected {self.dimensions})")
                results.append((embedding, elapsed_ms))
            
            logger.info(f"Generated {len(results)} embeddings in {elapsed_ms:.2f}ms")
            return results
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise


# Global embedding service instance
_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """Get or create global embedding service instance"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service

