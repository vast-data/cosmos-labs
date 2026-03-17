import os
import json
from typing import Any, Optional, Dict, List
from pydantic import BaseModel


class Settings(BaseModel):
    """Configuration settings for reasoning embedder"""
    # Embedding settings (NVIDIA NIM)
    embeddinghost: str
    embeddingport: int
    embeddinghttpscheme: str = "http"
    embedding_local_nim: bool = False
    embeddingmodel: str
    embeddingdimensions: int
    nvidia_api_key: Optional[str] = None  # Optional NVIDIA Cloud API key
    
    @classmethod
    def from_ctx_secrets(cls, secrets: Dict[str, str]) -> 'Settings':
        """Load settings from runtime context secrets (uses model defaults for missing optional fields)"""
        raw = secrets["videoreasonsecret"]
        config = {field: raw[field] for field in cls.__annotations__.keys() if field in raw}
        return cls(**config)


class ReasoningEvent(BaseModel):
    """Event data from video-reasoner"""
    source: str
    filename: str
    reasoning_content: str
    cosmos_model: str
    tokens_used: int
    processing_time: float
    video_url: str
    status: str = "success"
    
    # Metadata fields (passed through pipeline)
    is_public: bool = True  # Default to public (CLI uploads)
    allowed_users: str | None = None
    tags: str | None = None
    upload_timestamp: str | None = None
    segment_number: int | None = None
    total_segments: int | None = None
    segment_duration: float | None = None
    original_video: str | None = None

    # Stream capture metadata (from video-streaming service)
    camera_id: str | None = None
    capture_type: str | None = None
    location: str | None = None
    
    # Analysis scenario metadata
    scenario: str | None = None


class EmbeddingResult(BaseModel):
    """Result from embedding generation"""
    source: str
    filename: str
    reasoning_content: str
    embedding: List[float]
    embedding_model: str
    embedding_dimensions: int
    cosmos_model: str
    tokens_used: int
    processing_time: float
    video_url: str
    status: str = "success"
    
    # Metadata fields (passed to vastdb-writer)
    is_public: bool = True  # Default to public (CLI uploads)
    allowed_users: str | None = None
    tags: str | None = None
    upload_timestamp: str | None = None
    segment_number: int | None = None
    total_segments: int | None = None
    segment_duration: float | None = None
    original_video: str | None = None
    
    # Stream capture metadata (from video-streaming service)
    camera_id: str | None = None
    capture_type: str | None = None
    location: str | None = None
    
    # Analysis scenario metadata
    scenario: str | None = None

