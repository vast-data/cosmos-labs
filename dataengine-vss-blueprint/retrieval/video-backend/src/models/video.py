"""
Video models for database and API
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class VideoSegment(BaseModel):
    """Video segment metadata stored in VastDB"""
    filename: str
    source: str
    reasoning_content: str
    embedding: List[float]
    cosmos_model: str
    tokens_used: int
    processing_time: float
    video_url: str
    
    # Permission fields
    allowed_users: List[str] = Field(default_factory=list, description="List of usernames with access")
    is_public: bool = Field(default=True, description="Whether video is publicly accessible (default True)")
    
    # Metadata fields
    upload_timestamp: datetime
    duration: float
    segment_number: int
    total_segments: int
    original_video: str
    tags: List[str] = Field(default_factory=list, description="User-defined tags")
    
    # Search score (populated during similarity search)
    similarity_score: Optional[float] = None


class VideoSearchResult(BaseModel):
    """Video search result returned to frontend"""
    filename: str
    source: str
    reasoning_content: str
    video_url: str
    is_public: bool
    upload_timestamp: datetime
    duration: float
    segment_number: int
    total_segments: int
    original_video: str
    tags: List[str]
    similarity_score: float
    
    # Optional fields for display
    cosmos_model: Optional[str] = None
    tokens_used: Optional[int] = None

    # Stream capture metadata (from video-streaming service)
    camera_id: Optional[str] = None
    capture_type: Optional[str] = None
    neighborhood: Optional[str] = None


class VideoUploadMetadata(BaseModel):
    """Metadata for video upload"""
    filename: str
    is_public: bool = True  # Default to public (user can make it private)
    tags: List[str] = Field(default_factory=list)
    allowed_users: List[str] = Field(default_factory=list, description="Users with access (uploader always included)")

