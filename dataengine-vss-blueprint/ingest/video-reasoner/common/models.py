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
    
    # Provider selection: "cosmos" or "nemotron"
    reasoning_provider: str = Field(default="cosmos", description="Reasoning provider: 'cosmos' or 'nemotron'")
    
    # Cosmos settings (used when reasoning_provider == "cosmos")
    # Hosted Reason2 API - no SFTP needed, sends base64-encoded video directly
    cosmos_host: str = ""
    cosmos_port: int = 8001
    cosmos_model: str = ""
    cosmos_max_tokens: int = Field(default=4000, description="Maximum tokens in response for Cosmos (higher for detailed video analysis)")
    cosmos_temperature: float = Field(default=0.2, description="Sampling temperature for Cosmos")
    
    # Nemotron settings (used when reasoning_provider == "nemotron")
    nvidia_api_key: str = Field(default="", description="NVIDIA API key from build.nvidia.com")
    nemotron_model: str = Field(default="nvidia/nemotron-nano-12b-v2-vl", description="Nemotron model identifier")
    nemotron_endpoint: str = Field(default="https://integrate.api.nvidia.com/v1", description="Nemotron API endpoint")
    nemotron_num_frames: int = Field(default=5, description="Number of frames to extract from video (default: 5 for 5-second videos)")
    nemotron_frame_interval: Optional[float] = Field(default=None, description="Interval in seconds between frames (None = evenly spaced)")
    nemotron_max_tokens: int = Field(default=4096, description="Maximum tokens in response")
    nemotron_temperature: float = Field(default=0.6, description="Sampling temperature")
    nemotron_top_p: float = Field(default=0.7, description="Top-p sampling parameter")
    
    max_video_size_mb: int = 100
    # Scenario for prompt selection
    # Options: surveillance, traffic, nhl, sports, retail, warehouse, general
    scenario: str = "general"
    
    @computed_field
    @property
    def cosmos_url(self) -> str:
        """Compute Cosmos API URL"""
        return f"http://{self.cosmos_host}:{self.cosmos_port}/v1/chat/completions"
    
    @classmethod
    def from_ctx_secrets(cls, secrets: Dict[str, str]) -> 'Settings':
        """Load all settings from runtime context secrets"""
        field_names = cls.__annotations__.keys()
        config = {field: secrets["videoreasonsecret"][field] for field in field_names}
        return cls(**config)


class VideoReasoningResult(BaseModel):
    """Result from reasoning analysis (Cosmos or Nemotron)"""
    source: str
    filename: str
    reasoning_content: str
    cosmos_model: str = ""  # For backward compatibility, also used for nemotron_model
    tokens_used: int
    processing_time: float
    video_url: str = ""  # Optional, not used for Nemotron
    status: str = "success"
    reasoning_provider: str = "cosmos"  # "cosmos" or "nemotron"
    
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

