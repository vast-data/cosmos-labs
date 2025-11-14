import os
import json
from typing import Any, Optional, Dict
from pydantic import BaseModel, computed_field, Field


class Settings(BaseModel):
    """Configuration settings for video segmenter"""
    # S3 settings
    s3accesskey: str
    s3secretkey: str
    s3endpoint: str
    
    # Video processing settings
    segment_duration: int = 5  # seconds
    output_codec: str = "libx264"
    output_format: str = "mp4"
    output_bucket_suffix: str = "-segments"  # e.g., videos -> videos-segments
    
    @classmethod
    def from_ctx_secrets(cls, secrets: Dict[str, str]) -> 'Settings':
        """Load all settings from runtime context secrets"""
        field_names = cls.__annotations__.keys()
        config = {field: secrets["videoreasonsecret"][field] for field in field_names}
        return cls(**config)


class S3ObjectMetadataModel(BaseModel):
    """Pydantic model for parsing S3 metadata from video uploads"""
    
    # Metadata fields from frontend upload
    is_public: str | None = Field(None, alias="is-public")  # "true" or "false"
    allowed_users: str | None = Field(None, alias="allowed-users")  # Comma-separated usernames
    tags: str | None = None  # Comma-separated tags
    original_filename: str | None = Field(None, alias="original-filename")
    upload_timestamp: str | None = Field(None, alias="upload-timestamp")
    
    class Config:
        extra = "allow"
        populate_by_name = True
    
    def get_is_public_bool(self) -> bool:
        """Convert is_public string to boolean"""
        if self.is_public:
            return self.is_public.lower() == "true"
        return False
    
    def get_allowed_users_list(self) -> list[str]:
        """Parse allowed_users from comma-separated string"""
        if not self.allowed_users:
            return []
        return [u.strip() for u in self.allowed_users.split(",") if u.strip()]
    
    def get_tags_list(self) -> list[str]:
        """Parse tags from comma-separated string"""
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(",") if t.strip()]


class VideoSegmentInfo(BaseModel):
    """Information about a video segment"""
    segment_number: int
    total_segments: int
    duration: float
    start_time: float
    end_time: float
    segment_key: str
    segment_size: int

