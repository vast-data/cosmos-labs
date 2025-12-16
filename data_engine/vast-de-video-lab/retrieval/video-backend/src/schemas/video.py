"""
Video upload and management schemas
"""
from pydantic import BaseModel, Field
from typing import List


class VideoUploadRequest(BaseModel):
    """Video upload metadata"""
    is_public: bool = Field(default=False, description="Make video publicly accessible")
    tags: List[str] = Field(default_factory=list, description="Tags for video categorization")
    allowed_users: List[str] = Field(default_factory=list, description="Additional users with access (if not public)")


class VideoUploadResponse(BaseModel):
    """Video upload response"""
    upload_url: str = Field(..., description="Presigned S3 URL for upload")
    object_key: str = Field(..., description="S3 object key")
    expires_in: int = Field(..., description="URL expiration time in seconds")
    fields: dict = Field(..., description="Presigned POST fields for S3 upload")
    metadata: dict = Field(..., description="Metadata for display only")


class VideoListResponse(BaseModel):
    """List of videos response"""
    videos: List[dict]
    total: int

