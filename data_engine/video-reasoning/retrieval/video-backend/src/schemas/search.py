"""
Search schemas for semantic video search
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from src.models.video import VideoSearchResult


class VideoSearchRequest(BaseModel):
    """Semantic video search request"""
    query: str = Field(..., description="Natural language search query")
    top_k: int = Field(default=10, ge=1, le=100, description="Number of results to return")
    tags: List[str] = Field(default_factory=list, description="Filter by tags")
    owner: str | None = Field(default=None, description="Filter by owner")
    include_public: bool = Field(default=True, description="Include public videos")
    use_llm: bool = Field(default=False, description="Enable AI-powered synthesis of results")


class LLMSynthesisResponse(BaseModel):
    """LLM synthesis response"""
    response: str = Field(description="AI-generated synthesis")
    segments_used: int = Field(description="Number of video segments used")
    segments_analyzed: List[str] = Field(default_factory=list, description="List of segment names analyzed")
    model: str = Field(description="LLM model name")
    tokens_used: int = Field(description="Total tokens used")
    processing_time: float = Field(description="Processing time in seconds")
    error: Optional[str] = Field(default=None, description="Error message if synthesis failed")


class VideoSearchResponse(BaseModel):
    """Semantic video search response"""
    results: List[VideoSearchResult]
    total: int
    query: str
    embedding_time_ms: float
    search_time_ms: float
    permission_filtered: int = Field(description="Number of results filtered by permissions")
    llm_synthesis: Optional[LLMSynthesisResponse] = Field(default=None, description="AI-powered synthesis of results")

