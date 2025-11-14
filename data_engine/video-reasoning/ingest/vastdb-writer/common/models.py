import os
import json
from typing import Any, Optional, Dict, List
from pydantic import BaseModel


class Settings(BaseModel):
    """Configuration settings for VastDB writer"""
    # VastDB settings
    vdbendpoint: str
    vdbbucket: str
    vdbschema: str
    vdbaccesskey: str
    vdbsecretkey: str
    vdbcollection: str
    
    # For schema definition
    embeddingdimensions: int
    embeddingmodel: str
    
    @classmethod
    def from_ctx_secrets(cls, secrets: Dict[str, str]) -> 'Settings':
        """Load all settings from runtime context secrets"""
        field_names = cls.__annotations__.keys()
        config = {field: secrets["videoreasonsecret"][field] for field in field_names}
        return cls(**config)


class EmbeddingEvent(BaseModel):
    """Event data from reasoning-embedder"""
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
    
    # Metadata fields (from pipeline)
    is_public: bool = True  # Default to public (CLI uploads)
    allowed_users: str | None = None  # Empty for CLI uploads
    tags: str | None = None
    upload_timestamp: str | None = None
    segment_number: int | None = None
    total_segments: int | None = None
    segment_duration: float | None = None
    original_video: str | None = None

