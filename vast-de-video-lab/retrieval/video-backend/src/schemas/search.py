"""
Search schemas for semantic video search
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from src.models.video import VideoSearchResult


class VideoSearchRequest(BaseModel):
    """Semantic video search request"""
    query: str = Field(..., description="Natural language search query")
    top_k: int = Field(default=15, ge=1, le=100, description="Number of results to return from database")
    tags: List[str] = Field(default_factory=list, description="Filter by tags")
    owner: str | None = Field(default=None, description="Filter by owner")
    include_public: bool = Field(default=True, description="Include public videos")
    use_llm: bool = Field(default=False, description="Enable AI-powered synthesis of results")
    system_prompt: Optional[str] = Field(default=None, description="Custom LLM system prompt (overrides default from ConfigMap)")
    time_filter: str = Field(default="all", description="Time filter: 'all', '5m', '15m', '1h', '24h', '7d', 'custom'")
    custom_start_date: Optional[str] = Field(default=None, description="Custom start date (ISO 8601 format)")
    custom_end_date: Optional[str] = Field(default=None, description="Custom end date (ISO 8601 format)")
    metadata_filters: Dict[str, Any] = Field(default_factory=dict, description="Dynamic metadata filters (e.g., {'camera_id': 'CAM-001', 'neighborhood': 'Midtown'})")
    min_similarity: float = Field(default=0.1, ge=0.0, le=1.0, description="Minimum similarity score threshold (0.3-0.8 recommended)")
    llm_top_n: int = Field(default=3, ge=1, le=20, description="Number of top results to send to LLM for analysis")


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
    sql_query: Optional[str] = Field(default=None, description="Formatted SQL query executed against VastDB (user-friendly format)")

