import logging
import requests
from typing import List


class EmbeddingClient:
    """NVIDIA NIM embedding client - supports both hosted NIMs and NVIDIA cloud models"""

    def __init__(self, settings):
        self.model = settings.embeddingmodel
        self.dimensions = settings.embeddingdimensions
        self.nvidia_api_key = getattr(settings, "nvidia_api_key", None) or ""
        # embedding_local_nim only controls API key usage; always use configured host/port
        self.is_cloud = not getattr(settings, "embedding_local_nim", False)
        self.base_url = f"{settings.embeddinghttpscheme}://{settings.embeddinghost}:{settings.embeddingport}/v1"
        if self.is_cloud:
            logging.info(f"[EMBEDDING] Using NVIDIA Cloud: {self.base_url}")
        else:
            logging.info(f"[EMBEDDING] Using local NIM: {self.base_url}")

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings from NVIDIA NIM (hosted or cloud)"""
        headers = {"Content-Type": "application/json"}
        
        # Add API key when using NVIDIA Cloud (not when using local NIM)
        if self.is_cloud and self.nvidia_api_key:
            headers["Authorization"] = f"Bearer {self.nvidia_api_key}"
        
        payload = {
            "model": self.model,
            "input": texts,
            "input_type": "passage"  # Use "passage" for documents, "query" for search queries
        }

        logging.info(f"[EMBEDDING] Requesting embeddings for {len(texts)} texts using {'NVIDIA Cloud' if self.is_cloud else 'hosted NIM'}")
        
        request_url = f"{self.base_url}/embeddings"
        logging.info(f"[EMBEDDING] Request URL: {request_url}")
        logging.info(f"[EMBEDDING] Model: {self.model}, texts_count: {len(texts)}")
        
        response = requests.post(request_url, json=payload, headers=headers, timeout=60)

        if response.status_code != 200:
            logging.error(f"[EMBEDDING] NIM API Error {response.status_code}: {response.text}")
            logging.error(f"[EMBEDDING] Request URL: {request_url}")
            logging.error(f"[EMBEDDING] Model: {self.model}")

        response.raise_for_status()

        result = response.json()
        embeddings = [item["embedding"] for item in result["data"]]
        
        logging.info(f"[EMBEDDING] Received {len(embeddings)} embeddings")
        if embeddings:
            logging.info(f"[EMBEDDING] First embedding vector length: {len(embeddings[0])}")
            logging.info(f"[EMBEDDING] Embedding data type: {type(embeddings[0][0])}")
        
        return embeddings

