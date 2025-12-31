import os
import json
from typing import Any, Optional, Dict
from pydantic import BaseModel, computed_field, Field


class Settings(BaseModel):
    """Configuration settings for video reasoner"""
    # S3 settings
    s3accesskey: str
    s3secretkey: str
    s3endpoint: str
    
    # Cosmos settings
    cosmos_host: str
    cosmos_port: int
    cosmos_username: str
    cosmos_password: str
    cosmos_upload_path: str
    cosmos_video_port: int
    cosmos_model: str
    max_video_size_mb: int = 100
    # Scenario for prompt selection
    # Options: surveillance, traffic, nhl, sports, retail, warehouse, general
    scenario: str = "surveillance"
    
    @computed_field
    @property
    def cosmos_url(self) -> str:
        """Compute Cosmos API URL"""
        return f"http://{self.cosmos_host}:{self.cosmos_port}/v1/chat/completions"
    
    @computed_field
    @property
    def cosmos_ssh_host(self) -> str:
        """Compute Cosmos SSH host (same as cosmos_host)"""
        return self.cosmos_host
    
    @classmethod
    def from_ctx_secrets(cls, secrets: Dict[str, str]) -> 'Settings':
        """Load all settings from runtime context secrets"""
        field_names = cls.__annotations__.keys()
        config = {field: secrets["videoreasonsecret"][field] for field in field_names}
        return cls(**config)


class VideoReasoningResult(BaseModel):
    """Result from Cosmos reasoning analysis"""
    source: str
    filename: str
    reasoning_content: str
    cosmos_model: str
    tokens_used: int
    processing_time: float
    video_url: str
    status: str = "success"
    
    # Metadata fields from S3 (passed through pipeline)
    is_public: bool = True  # Default to public (for CLI uploads)
    allowed_users: str | None = None  # Comma-separated
    tags: str | None = None  # Comma-separated
    upload_timestamp: str | None = None
    segment_number: int | None = None
    total_segments: int | None = None
    segment_duration: float | None = None
    original_video: str | None = None

    # Stream capture metadata (from video-streaming service)
    camera_id: str | None = None
    capture_type: str | None = None
    neighborhood: str | None = None

